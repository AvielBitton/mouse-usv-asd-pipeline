from openpyxl import Workbook


def create_segmentation_workbook():
    """Create and initialize Excel workbook for segmentation results."""
    book = Workbook()
    sheet = book.active
    title = ['Path','Mother','Mother Genotype','Name','Sex','Offspring Genotype','Day','Session','Recording Number','Start point(s)','End point(s)','Duration (time)']
    sheet.append(title)
    return (book, sheet)
