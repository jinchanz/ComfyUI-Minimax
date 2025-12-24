import json
import requests
import time
import asyncio
import aiohttp
import base64
import torch
import numpy as np
from PIL import Image
import io
from .logging import logger


# MiniMax API 基础 URL
MINIMAX_API_BASE = "https://api.minimaxi.com"


def _image_tensor_to_base64(image_tensor, mime_type="image/png"):
    """将 ComfyUI 图片 tensor 转换为 base64 data URI"""
    # ComfyUI 图片格式: (B, H, W, C) 或 (H, W, C)，值范围 [0, 1]
    # 转换为 PIL Image
    if len(image_tensor.shape) == 4:
        # 取第一张图片
        image_tensor = image_tensor[0]
    
    # 确保是 3D tensor (H, W, C)
    if len(image_tensor.shape) != 3:
        raise ValueError(f"不支持的图片 tensor 形状: {image_tensor.shape}")
    
    # 转换为 numpy array，值范围 [0, 255]
    image_np = (image_tensor.cpu().numpy() * 255).astype(np.uint8)
    
    # 转换为 PIL Image
    channels = image_np.shape[2]
    if channels == 4:  # RGBA
        image = Image.fromarray(image_np, 'RGBA')
        # MiniMax API 支持 PNG，可以保留 RGBA
        # 但如果需要 JPEG，转换为 RGB
        if mime_type == "image/jpeg":
            # 创建白色背景并合成
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3])
            image = rgb_image
    elif channels == 3:  # RGB
        image = Image.fromarray(image_np, 'RGB')
    else:
        raise ValueError(f"不支持的通道数: {channels}")
    
    # 转换为 base64
    buffer = io.BytesIO()
    # 根据 mime_type 确定格式
    if mime_type == "image/jpeg":
        image_format = 'JPEG'
        # 确保是 RGB 模式
        if image.mode != 'RGB':
            image = image.convert('RGB')
    else:  # 默认使用 PNG
        image_format = 'PNG'
        mime_type = "image/png"
    
    image.save(buffer, format=image_format)
    image_bytes = buffer.getvalue()
    base64_str = base64.b64encode(image_bytes).decode('utf-8')
    
    # 返回 data URI
    return f"data:{mime_type};base64,{base64_str}"


def _process_image_input(image_input, image_url_input):
    """处理图片输入：优先使用 IMAGE tensor，否则使用 URL 字符串"""
    if image_input is not None:
        # 检查是否是 tensor
        if isinstance(image_input, torch.Tensor):
            # 转换为 base64 data URI
            return _image_tensor_to_base64(image_input)
        elif isinstance(image_input, (list, tuple)) and len(image_input) > 0:
            # 如果是列表，取第一个
            if isinstance(image_input[0], torch.Tensor):
                return _image_tensor_to_base64(image_input[0])
    
    # 如果没有提供 IMAGE tensor，使用 URL 字符串
    if image_url_input and image_url_input.strip():
        return image_url_input.strip()
    
    return None


def _poll_video_task(task_id, api_key, poll_interval, max_wait_time):
    """轮询视频生成任务结果"""
    query_url = f"{MINIMAX_API_BASE}/v1/query/video_generation"
    headers = {
        "Authorization": f"Bearer {api_key}" if api_key else ""
    }
    
    start_time = time.time()
    
    while True:
        try:
            # 检查是否超时
            if time.time() - start_time > max_wait_time:
                error_msg = f"任务轮询超时 ({max_wait_time}秒)"
                logger.info(f"[MiniMax] {error_msg}")
                return {"error": error_msg, "task_id": task_id}
            
            logger.info(f"[MiniMax] 轮询任务状态: {task_id}")
            
            # 查询任务状态
            response = requests.get(query_url, headers=headers, params={"task_id": task_id}, timeout=10)
            response.raise_for_status()
            
            result_data = response.json()
            task_status = result_data.get("status", "")
            
            logger.info(f"[MiniMax] 任务状态: {task_status}")
            
            # 任务完成
            if task_status == "Success":
                logger.info(f"[MiniMax] 任务完成成功")
                return result_data
            
            # 任务失败
            elif task_status == "Fail":
                error_msg = result_data.get("base_resp", {}).get("status_msg", "任务执行失败")
                logger.info(f"[MiniMax] 任务执行失败: {error_msg}")
                return result_data
            
            # 继续等待
            elif task_status in ["Preparing", "Queueing", "Processing"]:
                time.sleep(poll_interval)
                continue
            
            # 未知状态
            else:
                logger.info(f"[MiniMax] 未知任务状态: {task_status}")
                return result_data
                
        except requests.exceptions.RequestException as e:
            error_msg = f"轮询请求失败: {str(e)}"
            logger.info(f"[MiniMax] {error_msg}")
            return {"error": error_msg, "task_id": task_id}
            
        except Exception as e:
            error_msg = f"轮询过程出错: {str(e)}"
            logger.info(f"[MiniMax] {error_msg}")
            return {"error": error_msg, "task_id": task_id}


async def _async_poll_video_task(session, task_id, api_key, poll_interval, max_wait_time):
    """异步轮询视频生成任务结果"""
    query_url = f"{MINIMAX_API_BASE}/v1/query/video_generation"
    headers = {
        "Authorization": f"Bearer {api_key}" if api_key else ""
    }
    
    start_time = time.time()
    
    while True:
        try:
            # 检查是否超时
            if time.time() - start_time > max_wait_time:
                error_msg = f"任务轮询超时 ({max_wait_time}秒)"
                logger.info(f"[MiniMax] {error_msg}")
                return {"error": error_msg, "task_id": task_id}
            
            logger.info(f"[MiniMax] 轮询任务状态: {task_id}")
            
            # 查询任务状态
            async with session.get(query_url, headers=headers, params={"task_id": task_id}) as response:
                response.raise_for_status()
                result_data = await response.json()
            
            task_status = result_data.get("status", "")
            logger.info(f"[MiniMax] 任务状态: {task_status}")
            
            # 任务完成
            if task_status == "Success":
                logger.info(f"[MiniMax] 任务完成成功")
                return result_data
            
            # 任务失败
            elif task_status == "Fail":
                error_msg = result_data.get("base_resp", {}).get("status_msg", "任务执行失败")
                logger.info(f"[MiniMax] 任务执行失败: {error_msg}")
                return result_data
            
            # 继续等待
            elif task_status in ["Preparing", "Queueing", "Processing"]:
                await asyncio.sleep(poll_interval)
                continue
            
            # 未知状态
            else:
                logger.info(f"[MiniMax] 未知任务状态: {task_status}")
                return result_data
                
        except Exception as e:
            error_msg = f"轮询过程出错: {str(e)}"
            logger.info(f"[MiniMax] {error_msg}")
            return {"error": error_msg, "task_id": task_id}


def _get_video_download_url(file_id, api_key):
    """获取视频下载 URL"""
    retrieve_url = f"{MINIMAX_API_BASE}/v1/files/retrieve"
    headers = {
        "Authorization": f"Bearer {api_key}" if api_key else ""
    }
    
    try:
        response = requests.get(retrieve_url, headers=headers, params={"file_id": file_id}, timeout=10)
        response.raise_for_status()
        result_data = response.json()
        
        download_url = result_data.get("file", {}).get("download_url", "")
        if download_url:
            logger.info(f"[MiniMax] 获取下载 URL 成功: {download_url}")
            return download_url
        else:
            error_msg = "未找到下载 URL"
            logger.info(f"[MiniMax] {error_msg}")
            return None
            
    except Exception as e:
        error_msg = f"获取下载 URL 失败: {str(e)}"
        logger.info(f"[MiniMax] {error_msg}")
        return None


async def _async_get_video_download_url(session, file_id, api_key):
    """异步获取视频下载 URL"""
    retrieve_url = f"{MINIMAX_API_BASE}/v1/files/retrieve"
    headers = {
        "Authorization": f"Bearer {api_key}" if api_key else ""
    }
    
    try:
        async with session.get(retrieve_url, headers=headers, params={"file_id": file_id}) as response:
            response.raise_for_status()
            result_data = await response.json()
        
        download_url = result_data.get("file", {}).get("download_url", "")
        if download_url:
            logger.info(f"[MiniMax] 获取下载 URL 成功: {download_url}")
            return download_url
        else:
            error_msg = "未找到下载 URL"
            logger.info(f"[MiniMax] {error_msg}")
            return None
            
    except Exception as e:
        error_msg = f"获取下载 URL 失败: {str(e)}"
        logger.info(f"[MiniMax] {error_msg}")
        return None


def _create_and_poll_video_task(request_data, api_key, poll_interval, max_wait_time):
    """创建视频生成任务并轮询结果，最后获取下载 URL"""
    endpoint = f"{MINIMAX_API_BASE}/v1/video_generation"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}" if api_key else ""
    }
    
    try:
        logger.info(f"[MiniMax] 发送请求到: {endpoint}, 请求数据: {json.dumps(request_data, ensure_ascii=False)}")
        
        # 提交任务
        response = requests.post(endpoint, headers=headers, json=request_data, timeout=30)
        response.raise_for_status()
        response_data = response.json()
        
        logger.info(f"[MiniMax] 请求成功: {json.dumps(response_data, ensure_ascii=False)}")
        
        # 检查响应状态
        base_resp = response_data.get("base_resp", {})
        status_code = base_resp.get("status_code", -1)
        
        if status_code != 0:
            error_msg = base_resp.get("status_msg", "请求失败")
            logger.info(f"[MiniMax] 请求失败: {error_msg}")
            return {"error": error_msg, "base_resp": base_resp}
        
        # 获取 task_id
        task_id = response_data.get("task_id", "")
        if not task_id:
            error_msg = "未获取到 task_id"
            logger.info(f"[MiniMax] {error_msg}")
            return {"error": error_msg}
        
        logger.info(f"[MiniMax] 获取到任务ID: {task_id}")
        
        # 轮询任务状态
        task_result = _poll_video_task(task_id, api_key, poll_interval, max_wait_time)
        
        # 检查是否有错误
        if "error" in task_result:
            return task_result
        
        # 检查任务状态
        if task_result.get("status") != "Success":
            return task_result
        
        # 获取 file_id
        file_id = task_result.get("file_id", "")
        if not file_id:
            error_msg = "未获取到 file_id"
            logger.info(f"[MiniMax] {error_msg}")
            return {"error": error_msg, "task_result": task_result}
        
        # 获取下载 URL
        download_url = _get_video_download_url(file_id, api_key)
        if not download_url:
            return {"error": "获取下载 URL 失败", "task_result": task_result, "file_id": file_id}
        
        # 返回完整结果
        result = {
            "task_id": task_id,
            "file_id": file_id,
            "download_url": download_url,
            "status": "Success",
            "task_result": task_result
        }
        
        return result
        
    except requests.exceptions.RequestException as e:
        error_msg = f"API 请求失败: {str(e)}"
        logger.info(f"[MiniMax] {error_msg}")
        return {"error": error_msg}
        
    except Exception as e:
        error_msg = f"未知错误: {str(e)}"
        logger.info(f"[MiniMax] {error_msg}")
        return {"error": error_msg}


async def _async_create_and_poll_video_task(session, request_data, api_key, poll_interval, max_wait_time):
    """异步创建视频生成任务并轮询结果，最后获取下载 URL"""
    endpoint = f"{MINIMAX_API_BASE}/v1/video_generation"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}" if api_key else ""
    }
    
    try:
        logger.info(f"[MiniMax] 发送请求到: {endpoint}, 请求数据: {json.dumps(request_data, ensure_ascii=False)}")
        
        # 提交任务
        async with session.post(endpoint, headers=headers, json=request_data) as response:
            if response.status != 200:
                response_text = await response.text()
                raise ValueError(f"API 请求失败: {response.status} {response_text}")
            response_data = await response.json()
        
        logger.info(f"[MiniMax] 请求成功: {json.dumps(response_data, ensure_ascii=False)}")
        
        # 检查响应状态
        base_resp = response_data.get("base_resp", {})
        status_code = base_resp.get("status_code", -1)
        
        if status_code != 0:
            error_msg = base_resp.get("status_msg", "请求失败")
            logger.info(f"[MiniMax] 请求失败: {error_msg}")
            return {"error": error_msg, "base_resp": base_resp}
        
        # 获取 task_id
        task_id = response_data.get("task_id", "")
        if not task_id:
            error_msg = "未获取到 task_id"
            logger.info(f"[MiniMax] {error_msg}")
            return {"error": error_msg}
        
        logger.info(f"[MiniMax] 获取到任务ID: {task_id}")
        
        # 轮询任务状态
        task_result = await _async_poll_video_task(session, task_id, api_key, poll_interval, max_wait_time)
        
        # 检查是否有错误
        if "error" in task_result:
            return task_result
        
        # 检查任务状态
        if task_result.get("status") != "Success":
            return task_result
        
        # 获取 file_id
        file_id = task_result.get("file_id", "")
        if not file_id:
            error_msg = "未获取到 file_id"
            logger.info(f"[MiniMax] {error_msg}")
            return {"error": error_msg, "task_result": task_result}
        
        # 获取下载 URL
        download_url = await _async_get_video_download_url(session, file_id, api_key)
        if not download_url:
            return {"error": "获取下载 URL 失败", "task_result": task_result, "file_id": file_id}
        
        # 返回完整结果
        result = {
            "task_id": task_id,
            "file_id": file_id,
            "download_url": download_url,
            "status": "Success",
            "task_result": task_result
        }
        
        return result
        
    except Exception as e:
        error_msg = f"未知错误: {str(e)}"
        logger.info(f"[MiniMax] {error_msg}")
        return {"error": error_msg}


# ==================== 节点类定义 ====================

class MiniMaxTextToVideo:
    """文生视频节点"""
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("STRING", {"default": ""}),
                "model": (["MiniMax-Hailuo-2.3", "MiniMax-Hailuo-02", "T2V-01-Director", "T2V-01"], {"default": "MiniMax-Hailuo-2.3"}),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "prompt_optimizer": ("BOOLEAN", {"default": True}),
                "fast_pretreatment": ("BOOLEAN", {"default": False}),
                "duration": ("INT", {"default": 6, "min": 6, "max": 10}),
                "resolution": (["720P", "768P", "1080P"], {"default": "768P"}),
                "callback_url": ("STRING", {"default": ""}),
                "aigc_watermark": ("BOOLEAN", {"default": False}),
                "poll_interval": ("INT", {"default": 3, "min": 1, "max": 30}),
                "max_wait_time": ("INT", {"default": 600, "min": 30, "max": 3600}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    
    FUNCTION = "run"
    
    OUTPUT_NODE = True
    
    CATEGORY = "MiniMax"
    
    def run(self, api_key, model, prompt, prompt_optimizer=True, fast_pretreatment=False, 
            duration=6, resolution="768P", callback_url="", aigc_watermark=False,
            poll_interval=3, max_wait_time=600):
        try:
            if not prompt or prompt.strip() == "":
                raise ValueError("prompt 不能为空")
            
            # 构建请求数据
            request_data = {
                "model": model,
                "prompt": prompt,
                "prompt_optimizer": prompt_optimizer,
                "fast_pretreatment": fast_pretreatment,
                "duration": duration,
                "resolution": resolution,
                "aigc_watermark": aigc_watermark
            }
            
            if callback_url and callback_url.strip():
                request_data["callback_url"] = callback_url
            
            # 创建任务并轮询
            result = _create_and_poll_video_task(request_data, api_key, poll_interval, max_wait_time)
            
            return (json.dumps(result, ensure_ascii=False, indent=2),)
            
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            logger.info(f"[MiniMax TextToVideo] {error_msg}")
            return (json.dumps({"error": error_msg}, ensure_ascii=False),)


class MiniMaxImageToVideo:
    """图生视频节点"""
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("STRING", {"default": ""}),
                "model": (["MiniMax-Hailuo-2.3", "MiniMax-Hailuo-2.3-Fast", "MiniMax-Hailuo-02", "I2V-01-Director", "I2V-01-live", "I2V-01"], {"default": "MiniMax-Hailuo-2.3"}),
            },
            "optional": {
                "first_frame_image": ("IMAGE",),
                "first_frame_image_url": ("STRING", {"default": ""}),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "prompt_optimizer": ("BOOLEAN", {"default": True}),
                "fast_pretreatment": ("BOOLEAN", {"default": False}),
                "duration": ("INT", {"default": 6, "min": 6, "max": 10}),
                "resolution": (["512P", "720P", "768P", "1080P"], {"default": "768P"}),
                "callback_url": ("STRING", {"default": ""}),
                "aigc_watermark": ("BOOLEAN", {"default": False}),
                "poll_interval": ("INT", {"default": 3, "min": 1, "max": 30}),
                "max_wait_time": ("INT", {"default": 600, "min": 30, "max": 3600}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    
    FUNCTION = "run"
    
    OUTPUT_NODE = True
    
    CATEGORY = "MiniMax"
    
    def run(self, api_key, model, first_frame_image=None, first_frame_image_url="", prompt="", prompt_optimizer=True, 
            fast_pretreatment=False, duration=6, resolution="768P", callback_url="", 
            aigc_watermark=False, poll_interval=3, max_wait_time=600):
        try:
            # 处理图片输入
            processed_image = _process_image_input(first_frame_image, first_frame_image_url)
            if not processed_image:
                raise ValueError("first_frame_image 或 first_frame_image_url 必须提供其一")
            
            # 构建请求数据
            request_data = {
                "model": model,
                "first_frame_image": processed_image,
                "prompt_optimizer": prompt_optimizer,
                "fast_pretreatment": fast_pretreatment,
                "duration": duration,
                "resolution": resolution,
                "aigc_watermark": aigc_watermark
            }
            
            if prompt and prompt.strip():
                request_data["prompt"] = prompt
            
            if callback_url and callback_url.strip():
                request_data["callback_url"] = callback_url
            
            # 创建任务并轮询
            result = _create_and_poll_video_task(request_data, api_key, poll_interval, max_wait_time)
            
            return (json.dumps(result, ensure_ascii=False, indent=2),)
            
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            logger.info(f"[MiniMax ImageToVideo] {error_msg}")
            return (json.dumps({"error": error_msg}, ensure_ascii=False),)


class MiniMaxStartEndToVideo:
    """首尾帧生视频节点"""
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("STRING", {"default": ""}),
                "model": (["MiniMax-Hailuo-02"], {"default": "MiniMax-Hailuo-02"}),
            },
            "optional": {
                "first_frame_image": ("IMAGE",),
                "first_frame_image_url": ("STRING", {"default": ""}),
                "last_frame_image": ("IMAGE",),
                "last_frame_image_url": ("STRING", {"default": ""}),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "prompt_optimizer": ("BOOLEAN", {"default": True}),
                "duration": ("INT", {"default": 6, "min": 6, "max": 10}),
                "resolution": (["768P", "1080P"], {"default": "768P"}),
                "callback_url": ("STRING", {"default": ""}),
                "aigc_watermark": ("BOOLEAN", {"default": False}),
                "poll_interval": ("INT", {"default": 3, "min": 1, "max": 30}),
                "max_wait_time": ("INT", {"default": 600, "min": 30, "max": 3600}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    
    FUNCTION = "run"
    
    OUTPUT_NODE = True
    
    CATEGORY = "MiniMax"
    
    def run(self, api_key, model, first_frame_image=None, first_frame_image_url="", 
            last_frame_image=None, last_frame_image_url="", prompt="", 
            prompt_optimizer=True, duration=6, resolution="768P", callback_url="", 
            aigc_watermark=False, poll_interval=3, max_wait_time=600):
        try:
            # 处理首帧图片输入
            processed_first_image = _process_image_input(first_frame_image, first_frame_image_url)
            if not processed_first_image:
                raise ValueError("first_frame_image 或 first_frame_image_url 必须提供其一")
            
            # 处理尾帧图片输入
            processed_last_image = _process_image_input(last_frame_image, last_frame_image_url)
            if not processed_last_image:
                raise ValueError("last_frame_image 或 last_frame_image_url 必须提供其一")
            
            # 构建请求数据
            request_data = {
                "model": model,
                "first_frame_image": processed_first_image,
                "last_frame_image": processed_last_image,
                "prompt_optimizer": prompt_optimizer,
                "duration": duration,
                "resolution": resolution,
                "aigc_watermark": aigc_watermark
            }
            
            if prompt and prompt.strip():
                request_data["prompt"] = prompt
            
            if callback_url and callback_url.strip():
                request_data["callback_url"] = callback_url
            
            # 创建任务并轮询
            result = _create_and_poll_video_task(request_data, api_key, poll_interval, max_wait_time)
            
            return (json.dumps(result, ensure_ascii=False, indent=2),)
            
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            logger.info(f"[MiniMax StartEndToVideo] {error_msg}")
            return (json.dumps({"error": error_msg}, ensure_ascii=False),)


class MiniMaxSubjectReferenceToVideo:
    """主体参考生成视频节点"""
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("STRING", {"default": ""}),
                "model": (["S2V-01"], {"default": "S2V-01"}),
            },
            "optional": {
                "subject_image": ("IMAGE",),
                "subject_image_url": ("STRING", {"default": ""}),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "prompt_optimizer": ("BOOLEAN", {"default": True}),
                "callback_url": ("STRING", {"default": ""}),
                "aigc_watermark": ("BOOLEAN", {"default": False}),
                "poll_interval": ("INT", {"default": 3, "min": 1, "max": 30}),
                "max_wait_time": ("INT", {"default": 600, "min": 30, "max": 3600}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    
    FUNCTION = "run"
    
    OUTPUT_NODE = True
    
    CATEGORY = "MiniMax"
    
    def run(self, api_key, model, subject_image=None, subject_image_url="", prompt="", prompt_optimizer=True, 
            callback_url="", aigc_watermark=False, poll_interval=3, max_wait_time=600):
        try:
            # 处理主体图片输入
            processed_image = _process_image_input(subject_image, subject_image_url)
            if not processed_image:
                raise ValueError("subject_image 或 subject_image_url 必须提供其一")
            
            # 构建请求数据
            request_data = {
                "model": model,
                "subject_reference": [
                    {
                        "type": "character",
                        "image": [processed_image]
                    }
                ],
                "prompt_optimizer": prompt_optimizer,
                "aigc_watermark": aigc_watermark
            }
            
            if prompt and prompt.strip():
                request_data["prompt"] = prompt
            
            if callback_url and callback_url.strip():
                request_data["callback_url"] = callback_url
            
            # 创建任务并轮询
            result = _create_and_poll_video_task(request_data, api_key, poll_interval, max_wait_time)
            
            return (json.dumps(result, ensure_ascii=False, indent=2),)
            
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            logger.info(f"[MiniMax SubjectReferenceToVideo] {error_msg}")
            return (json.dumps({"error": error_msg}, ensure_ascii=False),)


# 节点映射
NODE_CLASS_MAPPINGS = {
    "MiniMaxTextToVideo": MiniMaxTextToVideo,
    "MiniMaxImageToVideo": MiniMaxImageToVideo,
    "MiniMaxStartEndToVideo": MiniMaxStartEndToVideo,
    "MiniMaxSubjectReferenceToVideo": MiniMaxSubjectReferenceToVideo,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MiniMaxTextToVideo": "MiniMax Text to Video",
    "MiniMaxImageToVideo": "MiniMax Image to Video",
    "MiniMaxStartEndToVideo": "MiniMax Start-End to Video",
    "MiniMaxSubjectReferenceToVideo": "MiniMax Subject Reference to Video",
}

