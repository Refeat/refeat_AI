from spire.pdf.common import *
from spire.pdf import *
import fitz  # PyMuPDF

# PDF 파일 로드
def merge_pdf_pages_into_one(pdf_path, output_path):
    pdf = PdfDocument(pdf_path)

    # 로드된 PDF의 페이지 너비와 페이지 높이 가져오기
    pageWidth = pdf.PageSettings.Width
    pageHeight = pdf.PageSettings.Height

    # 병합할 페이지의 시작 인덱스와 끝 인덱스를 지정
    startPageIndex = 0
    endPageIndex = pdf.Pages.Count - 1

    # 새 PDF 파일 생성
    newPdf = PdfDocument()

    # PDF 너비의 합인 새 페이지 너비를 생성합니다. 병합할 페이지
    newPageHeight = pageHeight * (endPageIndex - startPageIndex + 1)

    # 새 페이지 너비와 동일한 페이지 높이를 가진 새 페이지를 새 PDF 파일에 추가
    newPage = newPdf.Pages.Add(SizeF(pageWidth, newPageHeight), PdfMargins(0.0))

    # 초기 x 및 y 좌표 지정
    x = 0.0
    y = 0.0

    # 로드된 PDF에 병합할 페이지를 반복합니다
    for i in range(startPageIndex, endPageIndex + 1):
        page = pdf.Pages[i]
        # 새 PDF 파일의 새 페이지의 특정 위치에 각 페이지의 내용을 그립니다.
        newPage.Canvas.DrawTemplate(page.CreateTemplate(), PointF(x, y))
        y += pageHeight

    newPdf.SaveToFile(output_path)

    pdf.Close() 
    newPdf.Close()

def delete_text_from_pdf(input_pdf, output_pdf, text="Evaluation Warning : The document was created with Spire.PDF for Python."):
    doc = fitz.open(input_pdf)
    
    for page in doc: 
        text_instances = page.search_for(text)  # 삭제할 텍스트의 인스턴스를 찾습니다
        
        for inst in text_instances:
            page_width = page.rect.width
            rect = fitz.Rect(x0=0.0, y0=0.0, x1=page_width, y1=inst[3])  # Create a rectangle object
            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)   
   
    if input_pdf == output_pdf:
        doc.save(output_pdf, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
    else:
        doc.save(output_pdf)
    
if __name__ == '__main__':
    input_pdf =  "/home/ubuntu/refeat/s3_mount/pdf/07b56d28-0f89-4314-a82f-37a92a03bd43.pdf"
    output_pdf =  "/home/ubuntu/refeat/s3_mount/pdf/07b56d28-0f89-4314-a82f-37a92a03bd43_modified.pdf"
    output1_pdf =  "/home/ubuntu/refeat/s3_mount/pdf/07b56d28-0f89-4314-a82f-37a92a03bd43_modified_modified.pdf"
    merge_pdf_pages_into_one(input_pdf, output_pdf)
    delete_text_from_pdf(output_pdf, output1_pdf)

    