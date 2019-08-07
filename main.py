import PyPDF3
import sys
import io
import logging
import hashlib
from PIL import Image
from PIL import ImageColor

# Configure logging
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',level=logging.DEBUG)

def main():
    pf_pdf = PathfinderPDF('C:\\Users\\steph\\OneDrive\\Pathfinder\\PF2 Rulebooks\\AP Hellknight Hill\\PZO90145E.pdf')

    pf_pdf.SaveImages()

class PathfinderPDF:
    def __init__(self, pdfPath):
        logging.info(f'Importing PDF: {pdfPath}')
        self.pdf = PyPDF3.PdfFileReader(pdfPath)

        # Initialize min image size (KB)
        self.min_size = 150
        # Initialize empty list for images
        self.images = []

        # Some debug info
        logging.debug(f'PDF Encrypted   : {self.pdf.isEncrypted}')
        logging.debug(f'PDF Page Count  : {self.pdf.getNumPages()}')

        # Start retrieving images
        self.GetImages()
        
    
    def GetImages(self):

        for page_num, page in enumerate(self.pdf.pages):
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
                                    self.AppendImage(PathfinderImage(img, '.jpg'))
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
                                        self.AppendImage(PathfinderImage(img_combined, '.png'))

                                    # If no underlying mask is found, save base image
                                    else:
                                        #img.save(obj[1:] + ".jpg")
                                        logging.debug(f'Storing image.. Page: {page_num}, Image: {obj[1:]}. Type: /DCTDecode')
                                        self.AppendImage(PathfinderImage(img, '.jpg'))
     
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

        for img_num, img in enumerate(self.images):
            logging.debug(f'Saving image: images/{img_num}{img.extension}')
            img.image.save(f'images/{img_num}{img.extension}')

        logging.info('Image saving complete.')

class PathfinderImage:
    def __init__(self, image, extension):
        self.image = image
        self.extension = extension
    
    def __eq__(self, other):
        if self.image == other.image and self.extension == other.extension:
            return True
        else:
            return False

    def __len__(self):
        return sys.getsizeof(self.image.tobytes())


if __name__=="__main__":
    main()