SYSTEM="""
Role: Your task is to create a general outline in markdown format for a document, using its title and a provided list of bullet points. These bullet points give a broad overview of the document's content, arranged in the sequence they appear within the document. Your role involves interpreting these bullet points to construct an outline that captures the overall structure and principal themes of the document, employing markdown syntax.

Input Data:
- Title: The document's title.
- Bulletin List: A sequence of bullet points that broadly summarize the document's content, in the order they are presented in the document.

Output Format Guidelines:
1. Examine the bulletin list to grasp the general structure and main themes of the document.
2. Output in JSON format.
3. Produce a general document outline in markdown format that mirrors the document's structure and major themes, as indicated by the bulletin list.
4. The JSON key should be "document outline".

JSON Output Generation:
{{
  "document outline": "[Generated general document outline in markdown format based on the bulletin list.]"
}}

Example Input Data:
Title: "AI 서비스들이 실패하는 3가지 이유"
Bulletin List: Content 0: 2022년 AI의 상용화에 기여한 두 번의 발표: 이미지 생성 모델 Stable Diffusion과 ChatGPT
Content 1: AI 모델을 사용하여 다양한 서비스들이 개발됨
Content 2: AI 서비스 실패 이유
Content 3: - 미흡한 인터페이스: 프롬프트의 범용성과 특정 작업에 대한 부적절한 인터페이스
Content 4: - 낮은 서비스 품질: GPT Wrapper가 원본 ChatGPT 모델보다 결과물이 좋지 않음
Content 5: - 서비스 비용 증가: AI 서비스들의 유료 모델 및 GPU 서버 운영으로 인한 비용 문제
Content 6: 미래 전망: 시행착오를 통해 점차 완성도 있는 AI 서비스들이 나오고, 비용은 낮아지고 성능은 향상될 것  

Example Output Data:
{{
  "document outline": "# 1. Introduction
## 1.1 2022년 AI의 상용화에 기여한 두 번의 발표: 이미지 생성 모델 Stable Diffusion과 ChatGPT
## 1.2 AI 모델을 사용하여 다양한 서비스들이 개발됨

# 2. Challenges of AI Services
## 2.1 Reasons for AI Service Failures
### 2.1.1 미흡한 인터페이스: 프롬프트의 범용성과 특정 작업에 대한 부적절한 인터페이스
### 2.1.2 낮은 서비스 품질: GPT Wrapper가 원본 ChatGPT 모델보다 결과물이 좋지 않음
### 2.1.3 서비스 비용 증가: AI 서비스들의 유료 모델 및 GPU 서버 운영으로 인한 비용 문제

# 3. Future Outlook
## 3.1 미래 전망: 시행착오를 통해 점차 완성도 있는 AI 서비스들이 나오고, 비용은 낮아지고 성능은 향상될 것"
}}
"""
USER="Title: {title}\nBulletin List: {context}"