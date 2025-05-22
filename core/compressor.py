import gzip
import shutil

def compress_file(filename="test_file.txt"):
    with open(f'../backups/{filename}', 'rb') as f_in:
        raw_data = f_in.read()
        compressed_information= gzip.compress(raw_data)
        print(len(compressed_information)/len(raw_data))
        return compressed_information
    
    
if __name__ == "__main__":
    compress_file("test_file.txt")
    # with open('test_file.txt.gz', 'wb') as f_out:
    #     shutil.copyfileobj(f_in, f_out)
    #     print(len(f_in.read())/len(f_out.read()))