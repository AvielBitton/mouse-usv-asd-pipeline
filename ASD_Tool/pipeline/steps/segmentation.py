import numpy as np
from openpyxl import Workbook


def create_segmentation_workbook():
    """Create and initialize Excel workbook for segmentation results."""
    book = Workbook()
    sheet = book.active
    title = ['Path','Mother','Mother Genotype','Name','Sex','Offspring Genotype','Day','Session','Recording Number','Start point(s)','End point(s)','Duration (time)']
    sheet.append(title)
    return (book, sheet)


def trim_leading_silence(signal):
    """
    Remove leading silence (zeros) from audio signal.
    
    This function detects and removes silent segments at the beginning of the signal.
    If the signal starts with zeros, it finds the first non-zero segment and shifts
    the signal to start from that point, effectively trimming the leading silence.
    
    The function uses a two-step detection:
    1. First checks if the signal starts with zeros
    2. If so, finds where the continuous zero sequence ends by detecting changes
       in the difference of differences of zero indices
    
    Args:
        signal: numpy array of audio signal values
        
    Returns:
        tuple: (trimmed_signal, ind2) where:
            - trimmed_signal: signal with leading silence removed (or original if no leading silence)
            - ind2: index array used for further processing, [[0],[0]] if no trimming occurred
    """
    # if there is a 'silent' start (zeros), skipping to the "real" start:
    ind = np.where(signal == 0)
    is_empty = ind[0].size == 0
    if not(is_empty) and ind[0][0] == 0:
      DiffInd = np.diff(np.diff(ind))
      ind2 = np.where(DiffInd != 0)
      is_empty = ind2[0].size == 0
      if not(is_empty):
        for i in range(0,len(signal)-int(ind2[0])):
          signal[i] = signal[i+int(ind2[0])]
        i = range(len(signal)-int(ind2[0]),len(signal))
        signal = np.delete(signal,i)
      else:
        ind2 = [[0],[0]]
    else:
      ind2 = [[0],[0]]
    return (signal, ind2)
