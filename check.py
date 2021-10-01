

import bcachefs




with bcachefs.BCacheFS('dataset.img') as data:
    
    print(data.read_file('test.txt').tobytes().decode('utf-8'))

