from pdf_loader.pdf_loader import PdfLoader


class Loader:
    def __init__(self, save_path=None):
        self.save_path = save_path
        self.loader = None

    def load_file(self, file_path):
        if file_path.endswith('.pdf'):
            self.loader = PdfLoader(file_path)
        else:
            raise NotImplementedError

        self.loader.load_file()

    def save_data(self, output_path):
        self.loader.save_data(output_path)