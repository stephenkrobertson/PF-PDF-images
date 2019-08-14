import PyPDF3
import sys
import io
import os
import logging
import hashlib
import tkinter as tk
import threading
from tkinter import ttk
from tkinter import filedialog

from PIL import Image
from PIL import ImageColor

# Configure logging
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',level=logging.DEBUG)

def main():
    root = tk.Tk()
    UIController = PFPDF_UIController(root)    
    root.mainloop()

    #pf_pdf = PathfinderPDF('C:\\Users\\Stephen\\OneDrive\\Pathfinder\\PF2 Rulebooks\\AP Hellknight Hill\\PZO90145E.pdf')

    #pf_pdf.SaveImages()

def ProcessPDF(uic):
    if uic.pdfPath:
        pf_pdf = PathfinderPDF(uic.pdfPath)
        pf_pdf.SaveImages()
    
    
class PFPDF_UIController:
    def __init__(self, master):
        self.master = master
        self.pdfPath = ''

        master.title('Pathfinder PDF Image Extractor')
        master.geometry('400x57')

        #tk.ttk.Style().theme_use('alt')
        logging.debug(f'tkinter theme: {tk.ttk.Style().theme_use()}')
        logging.debug(f'tkinter themes: {tk.ttk.Style().theme_names()}')

        self.frame = tk.Frame(master, bg='GRAY')
        self.frame.place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.98)
        
        # First row - select pdf box
        self.openPdfEntry = ttk.Entry(self.frame)
        self.openPdfEntry.grid(column=0, row=0,sticky='nesw', padx=1, pady=1)
        self.openPdfButton = ttk.Button(self.frame, text="Open", command=self.OpenFile)
        self.openPdfButton.grid(column=1, row=0, padx=1, pady=1)

        # Second row - Start button
        self.startProcessing = ttk.Button(self.frame, text="Start", command=lambda: ProcessPDF(self))
        self.startProcessing.grid(column=0, row=1, sticky='nesw', columnspan=2, padx=1, pady=1)

        # Third row - Progress Bar
        #self.progressBar = ttk.Progressbar(self.frame, orient='horizontal', mode='determinate')
        #self.progressBar.grid(column=0, row=2, sticky='nesw', columnspan=2, padx=1, pady=1)

        self.frame.columnconfigure(0, weight=1)

        #button.pack()

        #label = tk.Label(frame, text='This is a label', bg='yellow')
        #label.pack()(
    def OpenFile(self):
        fd = filedialog.askopenfilename(filetypes=[("pdf files","*.pdf")])
        logging.debug(f'Opened {fd}')

        self.openPdfEntry.delete(0, 'end')
        self.openPdfEntry.insert(0, fd)

        self.pdfPath = fd
        
        return fd
    

class PathfinderPDF:
    def __init__(self, pdfPath, **kwargs):
        logging.info(f'Importing PDF: {pdfPath}')
        self.pdf = PyPDF3.PdfFileReader(pdfPath)
        self.save_path = os.path.dirname(pdfPath) +'/images-' + os.path.basename(pdfPath).strip('.pdf')

        # Initialize min image size (KB)
        self.min_size = 50
        # Initialize empty list for images
        self.images = []

        if 'progressBar' in kwargs:
            self.progressBar = kwargs['progressBar']

        # Some debug info
        logging.debug(f'PDF Encrypted   : {self.pdf.isEncrypted}')
        logging.debug(f'PDF Page Count  : {self.pdf.getNumPages()}')

        # Start retrieving images
        self.GetImages()
        
    
    def GetImages(self):

        for page_num, page in enumerate(self.pdf.pages, 1):
            #print(page.getContents())
            #print(page['/Resources'])
            if (page_num < 1024):
                if '/XObject' in page['/Resources']:
                    xObject = page['/Resources']['/XObject'].getObject()
                    
                    logging.debug(xObject)
                    for obj in xObject:
                        if xObject[obj]['/Subtype'] == '/Image':
                            data = xObject[obj].getData()
                            size = (xObject[obj]['/Width'], xObject[obj]['/Height'])
                            if '/Filter' in xObject[obj]:
                                if xObject[obj]['/Filter'] == '/FlateDecode':
                                    logging.debug(f'Storing image.. Page: {page_num}, Image: {obj[1:]}. Type: /FlateDecode')
                                    # TODO double check this 'L' is probably not right type
                                    img = Image.frombytes('L', size, data)
                                    #img = Image.open(io.BytesIO(data))
                                    self.AppendImage(PathfinderImage(img, 'jpeg', page_num))
                                    #img.save(obj[1:] + ".jpg")
                                elif xObject[obj]['/Filter'] == '/DCTDecode':
                                    #img = Image.frombytes('L', size, data, 'raw', 'L')
                                    img = Image.open(io.BytesIO(data))

                                    if '/SMask' in xObject[obj]:
                                        #print('Object has /SMask')
                                        #print(xObject[obj]['/SMask'])
                                        data = xObject[obj]['/SMask'].getData()
                                        if xObject[obj]['/SMask']['/Filter'] == '/DCTDecode':
                                            img_mask = Image.open(io.BytesIO(data))
                                        elif xObject[obj]['/SMask']['/Filter'] == '/FlateDecode':                                      
                                            img_mask = Image.frombytes('L', size, data)

                                        #apply mask
                                        img_mask.putalpha
                                        img.putalpha                                  
                                        img_alpha = Image.new('RGBA', size, color=ImageColor.getrgb('rgba(0,0,0,0)'))
                                        img_combined = Image.composite(img, img_alpha, img_mask)
                                        #img_combined.save(obj[1:] + "-combined.png")

                                        logging.debug(f'Storing image.. Page: {page_num}, Image: {obj[1:]}. Type: /DCTDecode with Mask')
                                        self.AppendImage(PathfinderImage(img_combined, 'png', page_num))

                                    # If no underlying mask is found, save base image
                                    else:
                                        #img.save(obj[1:] + ".jpg")
                                        logging.debug(f'Storing image.. Page: {page_num}, Image: {obj[1:]}. Type: /DCTDecode')
                                        self.AppendImage(PathfinderImage(img, 'jpeg', page_num))
     
                                else:
                                    logging.warning(f'UNKNOWN TYPE: {xObject[obj]}')
                            else:
                                logging.warning(f'NO FILTER: {xObject[obj]}')
                        else:
                            logging.warning(f'/Subtype not /Image: {xObject[obj]}')

    def AppendImage(self, image):
        # Don't append if duplicate images
        if image not in self.images:
            # Don't append if too small
            if len(image) > self.min_size * 1024:
                self.images.append(image)
            else:
                logging.debug(f'Image too small: {len(image)/1024}KB')
        else:
            logging.debug('Duplicate image found, not appending.')
    
    def SaveImages(self):
        logging.info('Image saving starting..')
        os.mkdir(self.save_path)

        enumerationTracker = {}
        for img_num, img in enumerate(self.images):
            if img.page_num not in enumerationTracker:
                enumerationTracker[img.page_num] = 1

            logging.debug(f'Saving image: {self.save_path}/{img.page_num}-{enumerationTracker[img.page_num]}.{img.extension}')
            img.image.save(f'{self.save_path}/{img.page_num}-{enumerationTracker[img.page_num]}.{img.extension}')

            enumerationTracker[img.page_num]+=1

        logging.info('Image saving complete.')

class PathfinderImage:
    def __init__(self, image, extension, page_num):
        self.image = image
        self.extension = extension
        self.page_num = page_num
    
    def __eq__(self, other):
        if self.image == other.image and self.extension == other.extension:
            return True
        else:
            return False

    def __len__(self):
        #return sys.getsizeof(self.image.tobytes())
        img_file = io.BytesIO()
        self.image.save(img_file, format=self.extension)
        logging.debug(f'Image size: {img_file.tell()}')
        return img_file.tell()


if __name__=="__main__":
    main()