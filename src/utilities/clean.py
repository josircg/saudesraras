import os


def clean_pot_date(filename):
    with open(filename, 'r+') as fp:
        # read an store all lines into list
        lines = fp.readlines()
        # move file pointer to the beginning of a file
        fp.seek(0)
        # truncate the file
        fp.truncate()

        # start writing lines
        for line in lines:
            if not line.startswith('"POT-Creation-Date'):
                fp.write(line)


if __name__ == "__main__":
    for root, dirs, files in os.walk('locale', topdown=True):
        for name in files:
            if name == 'django.po':
                print(os.path.join(root, name))
                clean_pot_date(os.path.join(root, name))
                break
