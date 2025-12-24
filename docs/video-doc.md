# 文生视频生成任务

> 使用本接口输入文本内容，创建视频生成任务。



## OpenAPI

````yaml api-reference/video/generation/api/text-to-video.json post /v1/video_generation
openapi: 3.1.0
info:
  title: MiniMax API
  description: MiniMax video generation and file management API
  license:
    name: MIT
  version: 1.0.0
servers:
  - url: https://api.minimaxi.com
security:
  - bearerAuth: []
paths:
  /v1/video_generation:
    post:
      tags:
        - Video
      summary: Video Generation
      operationId: videoGeneration
      parameters:
        - name: Content-Type
          in: header
          required: true
          description: 请求体的媒介类型，请设置为 `application/json` 确保请求数据的格式为 JSON.
          schema:
            type: string
            enum:
              - application/json
            default: application/json
      requestBody:
        description: ''
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/VideoGenerationReq'
        required: true
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/VideoGenerationResp'
components:
  schemas:
    VideoGenerationReq:
      type: object
      required:
        - model
        - prompt
      properties:
        model:
          type: string
          description: |-
            模型名称。可用值：
             `MiniMax-Hailuo-2.3`, `MiniMax-Hailuo-02`, `T2V-01-Director`, `T2V-01`.
          enum:
            - MiniMax-Hailuo-2.3
            - MiniMax-Hailuo-02
            - T2V-01-Director
            - T2V-01
        prompt:
          type: string
          description: "视频的文本描述，最大 2000 字符。对于 `MiniMax-Hailuo-2.3`、`MiniMax-Hailuo-02` 和 `*-Director` 系列模型，支持使用 `[指令]` 语法进行运镜控制。\n可在 prompt 中通过 [指令] 格式添加运镜指令，以实现精确的镜头控制。\n\n- 支持 15 种运镜指令的指令:\n\t - 左右移: [左移], [右移]\n\t - 左右摇: [左摇], [右摇]\n\t - 推拉: [推进], [拉远]\n\t - 升降: [上升], [下降]\n\t - 上下摇: [上摇], [下摇]\n\t - 变焦: [变焦推近], [变焦拉远]\n\t - 其他: [晃动], [跟随], [固定]\n\n - 使用规则:\n\t - 组合运镜: 同一组 [] 内的多个指令会同时生效，如 [左摇,上升]，建议组合不超过 3 个\n\t - 顺序运镜: prompt 中前后出现的指令会依次生效，如 \"...[推进], 然后...[拉远]\"\n\t - 自然语言: 也支持通过自然语言描述运镜，但使用标准指令能获得更准确的响应 "
        prompt_optimizer:
          type: boolean
          description: 是否自动优化 `prompt`，默认为 `true`。设为 `false` 可进行更精确的控制
        fast_pretreatment:
          type: boolean
          description: >-
            是否缩短 `prompt_optimizer` 的优化耗时，默认为 false。仅对 `MiniMax-Hailuo-2.3` 和
            `MiniMax-Hailuo-02` 模型生效。
        duration:
          type: integer
          description: |-
            视频时长（秒），默认值为 6。其可用值与模型和分辨率相关：
            | Model |  720P |768P | 1080P |
            | :--- |:--- |:--- | :--- |
            | MiniMax-Hailuo-2.3 | - | `6` 或 `10` | `6` |
            | MiniMax-Hailuo-02 | - | `6` 或 `10` | `6` |
            | 其他模型 | `6` | - |`6` |  
        resolution:
          type: string
          description: |-
            视频分辨率。其可用值与模型相关：
            | Model | 6s | 10s |
            | :--- | :--- | :--- |
            | MiniMax-Hailuo-2.3 |  `768P` (默认), `1080P` |  `768P` (默认) |
            | MiniMax-Hailuo-02 |  `768P` (默认), `1080P` |  `768P` (默认) |
            | 其他模型 | `720P` (默认) | 不支持 |
          enum:
            - 720P
            - 768P
            - 1080P
        callback_url:
          type: string
          description: "接收任务状态更新通知的回调 URL。支持通过 callback_url 参数可以配置回调，以接收任务状态的更新的异步通知。\n\n地址验证：配置后，MiniMax 服务器会向 callback_url 发送一个 POST 请求，请求体中包含 challenge 字段。服务端需要在 3 秒内原样返回该 challenge 值以完成验证\n状态更新：验证成功后，每当任务状态变更时，MiniMax 都会向该 URL 推送最新的任务状态。推送的数据结构与调用查询视频生成任务接口的响应体一致\n\n回调返回的\"status\"包括以下状态：\n- `\"processing\"` - 生成中\n- `\"success\"` - 成功\n- `\"failed\"` - 失败\n\n```python\nfrom fastapi import FastAPI, HTTPException, Request\r\nimport json\r\n\r\napp = FastAPI()\r\n\r\n@app.post(\"/get_callback\")\r\nasync def get_callback(request: Request):\r\n    try:\r\n        json_data = await request.json()\r\n        challenge = json_data.get(\"challenge\")\r\n        if challenge is not None:\r\n            # Validation request, echo back challenge\r\n            return {\"challenge\": challenge}\r\n        else:\r\n            # Status update request, handle accordingly\r\n            # {\r\n            #     \"task_id\": \"115334141465231360\",\r\n            #     \"status\": \"success\",\r\n            #     \"file_id\": \"205258526306433\",\r\n            #     \"base_resp\": {\r\n            #         \"status_code\": 0,\r\n            #         \"status_msg\": \"success\"\r\n            #     }\r\n            # }\r\n            return {\"status\": \"success\"}\r\n    except Exception as e:\r\n        raise HTTPException(status_code=500, detail=str(e))\r\n\r\nif __name__ == \"__main__\":\r\n    import uvicorn\r\n    uvicorn.run(\r\n        app,  # 必选\r\n        host=\"0.0.0.0\",  # 必选\r\n        port=8000,  # 必选，端口可设置\r\n        # ssl_keyfile=\"yourname.yourDomainName.com.key\",  # 可选，看是否开启ssl\r\n        # ssl_certfile=\"yourname.yourDomainName.com.key\",  # 可选，看是否开启ssl\r\n    )\n```"
        aigc_watermark:
          type: boolean
          description: 是否在生成的视频中添加水印，默认为 `false`
      example:
        model: MiniMax-Hailuo-2.3
        prompt: A man picks up a book [Pedestal up], then reads [Static shot].
        duration: 6
        resolution: 1080P
    VideoGenerationResp:
      type: object
      properties:
        task_id:
          type: string
          description: 视频生成任务的 ID，用于后续查询任务状态
        base_resp:
          $ref: '#/components/schemas/BaseResp'
      example:
        task_id: '106916112212032'
        base_resp:
          status_code: 0
          status_msg: success
    BaseResp:
      type: object
      properties:
        status_code:
          type: integer
          description: |-
            状态码及其分别含义如下：
            - 0：请求成功
            - 1002：触发限流，请稍后再试
            - 1004：账号鉴权失败，请检查 API-Key 是否填写正确
            - 1008：账号余额不足
            - 1026：视频描述涉及敏感内容，请调整
            - 2013：传入参数异常，请检查入参是否按要求填写
            - 2049：无效的api key，请检查api key

            更多内容可查看[错误码列表](/api-reference/errorcode)  
        status_msg:
          type: string
          description: 具体错误详情
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |-
        `HTTP: Bearer Auth`
         - Security Scheme Type: http
         - HTTP Authorization Scheme: Bearer API_key，用于验证账户信息，可在 [账户管理>接口密钥](https://platform.minimaxi.com/user-center/basic-information/interface-key) 中查看。

````

---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://platform.minimaxi.com/docs/llms.txt

# 图生视频任务

> 使用本接口输入图片及文本内容，创建视频生成任务。



## OpenAPI

````yaml api-reference/video/generation/api/image-to-video.json post /v1/video_generation
openapi: 3.1.0
info:
  title: MiniMax API
  description: MiniMax video generation and file management API
  license:
    name: MIT
  version: 1.0.0
servers:
  - url: https://api.minimaxi.com
security:
  - bearerAuth: []
paths:
  /v1/video_generation:
    post:
      tags:
        - Video
      summary: Video Generation
      operationId: videoGeneration
      parameters:
        - name: Content-Type
          in: header
          required: true
          description: 请求体的媒介类型，请设置为 `application/json` 确保请求数据的格式为 JSON.
          schema:
            type: string
            enum:
              - application/json
            default: application/json
      requestBody:
        description: ''
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/VideoGenerationReq'
        required: true
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/VideoGenerationResp'
components:
  schemas:
    VideoGenerationReq:
      type: object
      required:
        - model
        - first_frame_image
      properties:
        model:
          type: string
          description: >-
            模型名称。可用值： `MiniMax-Hailuo-2.3`, `MiniMax-Hailuo-2.3-Fast`,
            `MiniMax-Hailuo-02`, `I2V-01-Director`, `I2V-01-live`, `I2V-01`.  
          enum:
            - MiniMax-Hailuo-2.3
            - MiniMax-Hailuo-2.3-Fast
            - MiniMax-Hailuo-02
            - I2V-01-Director
            - I2V-01-live
            - I2V-01
        first_frame_image:
          type: string
          description: "将指定图片作为视频的起始帧。支持公网 URL 或 Base64 编码的 [Data URL](https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Schemes/data) (`data:image/jpeg;base64,...`)\n\n- 图片要求：\n\t- 格式：JPG, JPEG, PNG, WebP\n\t- 体积：小于 20MB\n\t- 尺寸：短边像素大于 300px，长宽比在 2:5 和 5:2 之间  "
        prompt:
          type: string
          description: "视频的文本描述，最大 2000 字符。对于 `MiniMax-Hailuo-2.3`、`MiniMax-Hailuo-2.3-Fast`、`MiniMax-Hailuo-02` 和 `I2V-01-Director` 系列模型，支持使用 `[指令]` 语法进行运镜控制。\n可在 prompt 中通过 [指令] 格式添加运镜指令，以实现精确的镜头控制。\n\n- 支持 15 种运镜指令的指令:\n\t - 左右移: [左移], [右移]\n\t - 左右摇: [左摇], [右摇]\n\t - 推拉: [推进], [拉远]\n\t - 升降: [上升], [下降]\n\t - 上下摇: [上摇], [下摇]\n\t - 变焦: [变焦推近], [变焦拉远]\n\t - 其他: [晃动], [跟随], [固定]\n\n - 使用规则:\n\t - 组合运镜: 同一组 [] 内的多个指令会同时生效，如 [左摇,上升]，建议组合不超过 3 个\n\t - 顺序运镜: prompt 中前后出现的指令会依次生效，如 \"...[推进], 然后...[拉远]\"\n\t - 自然语言: 也支持通过自然语言描述运镜，但使用标准指令能获得更准确的响应 "
        prompt_optimizer:
          type: boolean
          description: 是否自动优化 `prompt`，默认为 `true`。设为 `false` 可进行更精确的控制
        fast_pretreatment:
          type: boolean
          description: >-
            是否缩短 `prompt_optimizer` 的优化耗时，默认为 false。仅对
            `MiniMax-Hailuo-2.3`、`MiniMax-Hailuo-2.3-Fast` 和 `MiniMax-Hailuo-02`
            模型生效。
        duration:
          type: integer
          description: |-
            视频时长（秒），默认值为 6。其可用值与模型和分辨率相关：
            | Model |  720P |768P | 1080P |
            | :--- |:--- |:--- | :--- |
            | MiniMax-Hailuo-2.3 | - | `6` 或 `10` | `6` |
            | MiniMax-Hailuo-2.3-Fast | - | `6` 或 `10` | `6` |
            | MiniMax-Hailuo-02 | - | `6` 或 `10` | `6` |
            | 其他模型 | `6` | - |`6` |  
        resolution:
          type: string
          description: >-
            视频分辨率。其可用值与模型相关：

            | Model | 6s | 10s |

            | :--- | :--- | :--- |

            | MiniMax-Hailuo-2.3 | `768P` (默认), `1080P` | `768P` (默认) |

            | MiniMax-Hailuo-2.3-Fast | `768P` (默认), `1080P` | `768P` (默认) |

            | MiniMax-Hailuo-02 | `512P`, `768P` (默认), `1080P` | `512P`, `768P`
            (默认) |

            | 其他模型 | `720P` (默认) | 不支持 |
          enum:
            - 512P
            - 720P
            - 768P
            - 1080P
        callback_url:
          type: string
          description: "接收任务状态更新通知的回调 URL。支持通过 callback_url 参数可以配置回调，以接收任务状态的更新的异步通知。\n\n地址验证：配置后，MiniMax 服务器会向 callback_url 发送一个 POST 请求，请求体中包含 challenge 字段。服务端需要在 3 秒内原样返回该 challenge 值以完成验证\n状态更新：验证成功后，每当任务状态变更时，MiniMax 都会向该 URL 推送最新的任务状态。推送的数据结构与调用查询视频生成任务接口的响应体一致\n\n回调返回的\"status\"包括以下状态：\n- `\"processing\"` - 生成中\n- `\"success\"` - 成功\n- `\"failed\"` - 失败\n\n```python\nfrom fastapi import FastAPI, HTTPException, Request\r\nimport json\r\n\r\napp = FastAPI()\r\n\r\n@app.post(\"/get_callback\")\r\nasync def get_callback(request: Request):\r\n    try:\r\n        json_data = await request.json()\r\n        challenge = json_data.get(\"challenge\")\r\n        if challenge is not None:\r\n            # Validation request, echo back challenge\r\n            return {\"challenge\": challenge}\r\n        else:\r\n            # Status update request, handle accordingly\r\n            # {\r\n            #     \"task_id\": \"115334141465231360\",\r\n            #     \"status\": \"success\",\r\n            #     \"file_id\": \"205258526306433\",\r\n            #     \"base_resp\": {\r\n            #         \"status_code\": 0,\r\n            #         \"status_msg\": \"success\"\r\n            #     }\r\n            # }\r\n            return {\"status\": \"success\"}\r\n    except Exception as e:\r\n        raise HTTPException(status_code=500, detail=str(e))\r\n\r\nif __name__ == \"__main__\":\r\n    import uvicorn\r\n    uvicorn.run(\r\n        app,  # 必选\r\n        host=\"0.0.0.0\",  # 必选\r\n        port=8000,  # 必选，端口可设置\r\n        # ssl_keyfile=\"yourname.yourDomainName.com.key\",  # 可选，看是否开启ssl\r\n        # ssl_certfile=\"yourname.yourDomainName.com.key\",  # 可选，看是否开启ssl\r\n    )\n```"
        aigc_watermark:
          type: boolean
          description: 是否在生成的视频中添加水印，默认为 `false`
      example:
        prompt: A mouse runs toward the camera, smiling and blinking.
        first_frame_image: >-
          https://cdn.hailuoai.com/prod/2024-09-18-16/user/multi_chat_file/9c0b5c14-ee88-4a5b-b503-4f626f018639.jpeg
        model: MiniMax-Hailuo-2.3
        duration: 6
        resolution: 1080P
    VideoGenerationResp:
      type: object
      properties:
        task_id:
          type: string
          description: 视频生成任务的 ID，用于后续查询任务状态
        base_resp:
          $ref: '#/components/schemas/BaseResp'
      example:
        task_id: '106916112212032'
        base_resp:
          status_code: 0
          status_msg: success
    BaseResp:
      type: object
      properties:
        status_code:
          type: integer
          description: |-
            状态码及其分别含义如下：
            - 0：请求成功
            - 1002：触发限流，请稍后再试
            - 1004：账号鉴权失败，请检查 API-Key 是否填写正确
            - 1008：账号余额不足
            - 1026：视频描述涉及敏感内容，请调整
            - 2013：传入参数异常，请检查入参是否按要求填写
            - 2049：无效的api key，请检查api key

            更多内容可查看[错误码列表](/api-reference/errorcode)  
        status_msg:
          type: string
          description: 具体错误详情
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |-
        `HTTP: Bearer Auth`
         - Security Scheme Type: http
         - HTTP Authorization Scheme: Bearer API_key，用于验证账户信息，可在 [账户管理>接口密钥](https://platform.minimaxi.com/user-center/basic-information/interface-key) 中查看。

````

---
# 首尾帧生成视频

> 使用本接口上传首尾帧图片及文本内容，创建视频生成任务。



## OpenAPI

````yaml api-reference/video/generation/api/start-end-to-video.json post /v1/video_generation
openapi: 3.1.0
info:
  title: MiniMax API
  description: MiniMax video generation and file management API
  license:
    name: MIT
  version: 1.0.0
servers:
  - url: https://api.minimaxi.com
security:
  - bearerAuth: []
paths:
  /v1/video_generation:
    post:
      tags:
        - Video
      summary: Video Generation
      operationId: videoGeneration
      parameters:
        - name: Content-Type
          in: header
          required: true
          description: 请求体的媒介类型，请设置为 `application/json` 确保请求数据的格式为 JSON.
          schema:
            type: string
            enum:
              - application/json
            default: application/json
      requestBody:
        description: ''
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/VideoGenerationReq'
        required: true
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/VideoGenerationResp'
components:
  schemas:
    VideoGenerationReq:
      type: object
      required:
        - model
        - last_frame_image
      properties:
        model:
          type: string
          description: |-
            模型名称。可用值： `MiniMax-Hailuo-02`。

            注意：首尾帧生成功能不支持 512P 分辨率。
          enum:
            - MiniMax-Hailuo-02
        prompt:
          type: string
          description: "视频的文本描述，最大 2000 字符。对于 `MiniMax-Hailuo-02` ，支持使用 `[指令]` 语法进行运镜控制。\n可在 prompt 中通过 [指令] 格式添加运镜指令，以实现精确的镜头控制。\n\n- 支持 15 种运镜指令的指令:\n\t - 左右移: [左移], [右移]\n\t - 左右摇: [左摇], [右摇]\n\t - 推拉: [推进], [拉远]\n\t - 升降: [上升], [下降]\n\t - 上下摇: [上摇], [下摇]\n\t - 变焦: [变焦推近], [变焦拉远]\n\t - 其他: [晃动], [跟随], [固定]\n\n - 使用规则:\n\t - 组合运镜: 同一组 [] 内的多个指令会同时生效，如 [左摇,上升]，建议组合不超过 3 个\n\t - 顺序运镜: prompt 中前后出现的指令会依次生效，如 \"...[推进], 然后...[拉远]\"\n\t - 自然语言: 也支持通过自然语言描述运镜，但使用标准指令能获得更准确的响应 "
        first_frame_image:
          type: string
          description: "将指定图片作为视频的**起始帧**。支持公网 URL 或 Base64 编码的 [Data URL](https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Schemes/data) (`data:image/jpeg;base64,...`)\n\n- 图片要求：\n\t- 格式：JPG, JPEG, PNG, WebP\n\t- 体积：小于 20MB\n\t- 尺寸：短边像素大于 300px，长宽比在 2:5 和 5:2 之间 \n\n⚠️ 生成视频尺寸遵循首帧图片"
        last_frame_image:
          type: string
          description: "将指定图片作为视频的**结束帧**。支持公网 URL 或 Base64 编码的 [Data URL](https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Schemes/data) (`data:image/jpeg;base64,...`)\n\n- 图片要求：\n\t- 格式：JPG, JPEG, PNG, WebP\n\t- 体积：小于 20MB\n\t- 尺寸：短边像素大于 300px，长宽比在 2:5 和 5:2 之间\n\n⚠️ 生成视频尺寸遵循首帧图片，当首帧和尾帧的图片尺寸不一致时，模型将参考首帧对尾帧图片进行裁剪"
        prompt_optimizer:
          type: boolean
          description: 是否自动优化 `prompt`，默认为 `true`。设为 `false` 可进行更精确的控制
        duration:
          type: integer
          description: |-
            视频时长（秒），默认值为 6。首尾帧生成可用值与分辨率相关：

            | Model | 768P | 1080P |
            | :--- | :--- | :--- |
            | MiniMax-Hailuo-02 | `6` 或 `10` | `6` |
        resolution:
          type: string
          description: |-
            视频分辨率。首尾帧生成支持 768P 和 1080P：
            | Model | 6s | 10s |
            | :--- | :--- | :--- |
            | MiniMax-Hailuo-02 | `768P` (默认), `1080P` | `768P` |
          enum:
            - 768P
            - 1080P
        callback_url:
          type: string
          description: "接收任务状态更新通知的回调 URL。支持通过 callback_url 参数可以配置回调，以接收任务状态的更新的异步通知。\n\n地址验证：配置后，MiniMax 服务器会向 callback_url 发送一个 POST 请求，请求体中包含 challenge 字段。服务端需要在 3 秒内原样返回该 challenge 值以完成验证\n状态更新：验证成功后，每当任务状态变更时，MiniMax 都会向该 URL 推送最新的任务状态。推送的数据结构与调用查询视频生成任务接口的响应体一致\n\n回调返回的\"status\"包括以下状态：\n- `\"processing\"` - 生成中\n- `\"success\"` - 成功\n- `\"failed\"` - 失败\n\n```python\nfrom fastapi import FastAPI, HTTPException, Request\r\nimport json\r\n\r\napp = FastAPI()\r\n\r\n@app.post(\"/get_callback\")\r\nasync def get_callback(request: Request):\r\n    try:\r\n        json_data = await request.json()\r\n        challenge = json_data.get(\"challenge\")\r\n        if challenge is not None:\r\n            # Validation request, echo back challenge\r\n            return {\"challenge\": challenge}\r\n        else:\r\n            # Status update request, handle accordingly\r\n            # {\r\n            #     \"task_id\": \"115334141465231360\",\r\n            #     \"status\": \"success\",\r\n            #     \"file_id\": \"205258526306433\",\r\n            #     \"base_resp\": {\r\n            #         \"status_code\": 0,\r\n            #         \"status_msg\": \"success\"\r\n            #     }\r\n            # }\r\n            return {\"status\": \"success\"}\r\n    except Exception as e:\r\n        raise HTTPException(status_code=500, detail=str(e))\r\n\r\nif __name__ == \"__main__\":\r\n    import uvicorn\r\n    uvicorn.run(\r\n        app,  # 必选\r\n        host=\"0.0.0.0\",  # 必选\r\n        port=8000,  # 必选，端口可设置\r\n        # ssl_keyfile=\"yourname.yourDomainName.com.key\",  # 可选，看是否开启ssl\r\n        # ssl_certfile=\"yourname.yourDomainName.com.key\",  # 可选，看是否开启ssl\r\n    )\n```"
        aigc_watermark:
          type: boolean
          description: 是否在生成的视频中添加水印，默认为 `false`
      example:
        prompt: A little girl grow up.
        first_frame_image: >-
          https://filecdn.minimax.chat/public/fe9d04da-f60e-444d-a2e0-18ae743add33.jpeg
        last_frame_image: >-
          https://filecdn.minimax.chat/public/97b7cd08-764e-4b8b-a7bf-87a0bd898575.jpeg
        model: MiniMax-Hailuo-02
        duration: 6
        resolution: 1080P
    VideoGenerationResp:
      type: object
      properties:
        task_id:
          type: string
          description: 视频生成任务的 ID，用于后续查询任务状态
        base_resp:
          $ref: '#/components/schemas/BaseResp'
      example:
        task_id: '106916112212032'
        base_resp:
          status_code: 0
          status_msg: success
    BaseResp:
      type: object
      properties:
        status_code:
          type: integer
          description: |-
            状态码及其分别含义如下：
            - 0：请求成功
            - 1002：触发限流，请稍后再试
            - 1004：账号鉴权失败，请检查 API-Key 是否填写正确
            - 1008：账号余额不足
            - 1026：视频描述涉及敏感内容，请调整
            - 2013：传入参数异常，请检查入参是否按要求填写
            - 2049：无效的api key，请检查api key

            更多内容可查看[错误码列表](/api-reference/errorcode)  
        status_msg:
          type: string
          description: 具体错误详情
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |-
        `HTTP: Bearer Auth`
         - Security Scheme Type: http
         - HTTP Authorization Scheme: Bearer API_key，用于验证账户信息，可在 [账户管理>接口密钥](https://platform.minimaxi.com/user-center/basic-information/interface-key) 中查看。

````

---


# 主体参考视频生成任务

> 使用本接口上传人物主体图片及文本内容，创建视频生成任务。



## OpenAPI

````yaml api-reference/video/generation/api/subject-reference-to-video.json post /v1/video_generation
openapi: 3.1.0
info:
  title: MiniMax API
  description: MiniMax video generation and file management API
  license:
    name: MIT
  version: 1.0.0
servers:
  - url: https://api.minimaxi.com
security:
  - bearerAuth: []
paths:
  /v1/video_generation:
    post:
      tags:
        - Video
      summary: Video Generation
      operationId: videoGeneration
      parameters:
        - name: Content-Type
          in: header
          required: true
          description: 请求体的媒介类型，请设置为 `application/json` 确保请求数据的格式为 JSON.
          schema:
            type: string
            enum:
              - application/json
            default: application/json
      requestBody:
        description: ''
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/VideoGenerationReq'
        required: true
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/VideoGenerationResp'
components:
  schemas:
    VideoGenerationReq:
      type: object
      required:
        - model
        - subject_reference
      properties:
        model:
          type: string
          description: '模型名称。可用值： `S2V-01`.  '
          enum:
            - S2V-01
        prompt:
          type: string
          description: 视频的文本描述，最大 2000 字符.
        prompt_optimizer:
          type: boolean
          description: 是否自动优化 `prompt`，默认为 `true`。设为 `false` 可进行更精确的控制
        subject_reference:
          type: array
          items:
            $ref: '#/components/schemas/SubjectReference'
          description: 主体参考，仅当 `model` 为 `S2V-01` 时可用。目前仅支持单个主体
        callback_url:
          type: string
          description: "接收任务状态更新通知的回调 URL。支持通过 callback_url 参数可以配置回调，以接收任务状态的更新的异步通知。\n\n地址验证：配置后，MiniMax 服务器会向 callback_url 发送一个 POST 请求，请求体中包含 challenge 字段。服务端需要在 3 秒内原样返回该 challenge 值以完成验证\n状态更新：验证成功后，每当任务状态变更时，MiniMax 都会向该 URL 推送最新的任务状态。推送的数据结构与调用查询视频生成任务接口的响应体一致\n\n回调返回的\"status\"包括以下状态：\n- `\"processing\"` - 生成中\n- `\"success\"` - 成功\n- `\"failed\"` - 失败\n\n```python\nfrom fastapi import FastAPI, HTTPException, Request\r\nimport json\r\n\r\napp = FastAPI()\r\n\r\n@app.post(\"/get_callback\")\r\nasync def get_callback(request: Request):\r\n    try:\r\n        json_data = await request.json()\r\n        challenge = json_data.get(\"challenge\")\r\n        if challenge is not None:\r\n            # Validation request, echo back challenge\r\n            return {\"challenge\": challenge}\r\n        else:\r\n            # Status update request, handle accordingly\r\n            # {\r\n            #     \"task_id\": \"115334141465231360\",\r\n            #     \"status\": \"success\",\r\n            #     \"file_id\": \"205258526306433\",\r\n            #     \"base_resp\": {\r\n            #         \"status_code\": 0,\r\n            #         \"status_msg\": \"success\"\r\n            #     }\r\n            # }\r\n            return {\"status\": \"success\"}\r\n    except Exception as e:\r\n        raise HTTPException(status_code=500, detail=str(e))\r\n\r\nif __name__ == \"__main__\":\r\n    import uvicorn\r\n    uvicorn.run(\r\n        app,  # 必选\r\n        host=\"0.0.0.0\",  # 必选\r\n        port=8000,  # 必选，端口可设置\r\n        # ssl_keyfile=\"yourname.yourDomainName.com.key\",  # 可选，看是否开启ssl\r\n        # ssl_certfile=\"yourname.yourDomainName.com.key\",  # 可选，看是否开启ssl\r\n    )\n```"
        aigc_watermark:
          type: boolean
          description: 是否在生成的视频中添加水印，默认为 `false`
      example:
        prompt: A girl runs toward the camera and winks with a smile.
        subject_reference:
          - type: character
            image:
              - >-
                https://cdn.hailuoai.com/prod/2025-08-12-17/video_cover/1754990600020238321-411603868533342214-cover.jpg
        model: S2V-01
    VideoGenerationResp:
      type: object
      properties:
        task_id:
          type: string
          description: 视频生成任务的 ID，用于后续查询任务状态
        base_resp:
          $ref: '#/components/schemas/BaseResp'
      example:
        task_id: '106916112212032'
        base_resp:
          status_code: 0
          status_msg: success
    SubjectReference:
      type: object
      required:
        - type
        - image
      properties:
        type:
          type: string
          description: 主体类型，当前仅支持 `character` (人物面部)
        image:
          type: array
          items:
            type: string
          description: "包含主体参考图的数组（目前仅支持单张图片）\n\n- 图片要求：\n\t- 格式：JPG, JPEG, PNG, WebP\n\t- 体积：小于 20MB\n\t- 尺寸：短边像素大于 300px，长宽比在 2:5 和 5:2 之间  "
    BaseResp:
      type: object
      properties:
        status_code:
          type: integer
          description: |-
            状态码及其分别含义如下：
            - 0：请求成功
            - 1002：触发限流，请稍后再试
            - 1004：账号鉴权失败，请检查 API-Key 是否填写正确
            - 1008：账号余额不足
            - 1026：视频描述涉及敏感内容，请调整
            - 2013：传入参数异常，请检查入参是否按要求填写
            - 2049：无效的api key，请检查api key

            更多内容可查看[错误码列表](/api-reference/errorcode)
        status_msg:
          type: string
          description: 具体错误详情
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |-
        `HTTP: Bearer Auth`
         - Security Scheme Type: http
         - HTTP Authorization Scheme: Bearer API_key，用于验证账户信息，可在 [账户管理>接口密钥](https://platform.minimaxi.com/user-center/basic-information/interface-key) 中查看。

````

---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://platform.minimaxi.com/docs/llms.txt
# 查询视频生成任务状态

> 使用本接口查询视频生成的任务状态。



## OpenAPI

````yaml api-reference/video/generation/api/openapi.json get /v1/query/video_generation
openapi: 3.1.0
info:
  title: MiniMax API
  description: MiniMax video generation and file management API
  license:
    name: MIT
  version: 1.0.0
servers:
  - url: https://api.minimaxi.com
security:
  - bearerAuth: []
paths:
  /v1/query/video_generation:
    get:
      tags:
        - Video
      summary: Query Video Generation Task
      operationId: queryVideoGenerationTask
      parameters:
        - name: task_id
          in: query
          required: true
          description: 待查询的任务 ID。只能查询当前账号创建的任务
          schema:
            type: string
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/QueryVideoGenerationTaskResp'
components:
  schemas:
    QueryVideoGenerationTaskResp:
      type: object
      properties:
        task_id:
          type: string
          description: 被查询的任务 ID
        status:
          $ref: '#/components/schemas/VideoProcessStatus'
        file_id:
          type: string
          description: 任务成功时返回，用于获取视频文件的文件 ID
        video_width:
          type: integer
          description: 任务成功时返回，生成视频的宽度（像素）.
        video_height:
          type: integer
          description: 任务成功时返回，生成视频的高度（像素）
        base_resp:
          $ref: '#/components/schemas/QueryVideoGenerationTaskBaseResp'
      example:
        task_id: '176843862716480'
        status: Success
        file_id: '176844028768320'
        video_width: 1920
        video_height: 1080
        base_resp:
          status_code: 0
          status_msg: success
    VideoProcessStatus:
      type: string
      enum:
        - Preparing
        - Queueing
        - Processing
        - Success
        - Fail
      description: |-
        任务的当前状态。可能的状态值包括：
        - `Preparing` – 准备中
        - `Queueing` – 队列中
        - `Processing` – 生成中
        - `Success` – 成功
        - `Fail` – 失败
    QueryVideoGenerationTaskBaseResp:
      type: object
      properties:
        status_code:
          type: integer
          description: |-
            状态码及其分别含义如下：
            - 0：请求成功
            - 1002：触发限流，请稍后再试
            - 1004：账号鉴权失败，请检查 api key是否填写正确
            - 1026：输入内容涉及敏感内容
            - 1027：生成视频涉及敏感内容

            更多内容可查看[错误码查询列表](/api-reference/errorcode)了解详情
        status_msg:
          type: string
          description: 状态信息，成功时为 `success`.
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |-
        `HTTP: Bearer Auth`
         - Security Scheme Type: http
         - HTTP Authorization Scheme: Bearer API_key，用于验证账户信息，可在 [账户管理>接口密钥](https://platform.minimaxi.com/user-center/basic-information/interface-key) 中查看。

````

---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://platform.minimaxi.com/docs/llms.txt
# 视频下载

> 通过本接口进行生成视频文件下载。



## OpenAPI

````yaml api-reference/video/generation/api/openapi.json get /v1/files/retrieve
openapi: 3.1.0
info:
  title: MiniMax API
  description: MiniMax video generation and file management API
  license:
    name: MIT
  version: 1.0.0
servers:
  - url: https://api.minimaxi.com
security:
  - bearerAuth: []
paths:
  /v1/files/retrieve:
    get:
      tags:
        - Files
      summary: Retrieve File
      operationId: retrieveFile
      parameters:
        - name: file_id
          in: query
          required: true
          description: |-
            文件的唯一标识符
            支持视频任务状态查询接口获得的 `file_id`
          schema:
            type: integer
            format: int64
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RetrieveFileResp'
components:
  schemas:
    RetrieveFileResp:
      type: object
      properties:
        file:
          $ref: '#/components/schemas/FileObject'
        base_resp:
          $ref: '#/components/schemas/RetrieveFileBaseResp'
      example:
        file:
          file_id: ${file_id}
          bytes: 5896337
          created_at: 1700469398
          filename: output_aigc.mp4
          purpose: video_generation
          download_url: www.downloadurl.com
        base_resp:
          status_code: 0
          status_msg: success
    FileObject:
      type: object
      properties:
        file_id:
          type: integer
          format: int64
          description: 文件的唯一标识符
        bytes:
          type: integer
          format: int64
          description: 文件大小，以字节为单位
        created_at:
          type: integer
          format: int64
          description: 创建文件时的 Unix 时间戳，以秒为单位
        filename:
          type: string
          description: 文件的名称
        purpose:
          type: string
          description: 文件的使用目的
        download_url:
          type: string
          format: url
          description: 文件下载的url地址
    RetrieveFileBaseResp:
      type: object
      properties:
        status_code:
          type: integer
          description: |-
            状态码如下：
            - 1000, 未知错误
            - 1001, 超时
            - 1002, 触发RPM限流
            - 1004, 鉴权失败
            - 1008, 余额不足
            - 1013, 服务内部错误
            - 1026, 输入内容错误
            - 1027, 输出内容错误
            - 1039, 触发TPM限流
            - 2013, 输入格式信息不正常

            更多内容可查看[错误码查询列表](/api-reference/errorcode)了解详情
        status_msg:
          type: string
          description: 状态详情
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |-
        `HTTP: Bearer Auth`
         - Security Scheme Type: http
         - HTTP Authorization Scheme: Bearer API_key，用于验证账户信息，可在 [账户管理>接口密钥](https://platform.minimaxi.com/user-center/basic-information/interface-key) 中查看。

````

---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://platform.minimaxi.com/docs/llms.txt