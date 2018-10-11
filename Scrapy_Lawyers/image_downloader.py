import csv
import urllib.request


def main():
    with open('result.csv') as csvfile:
        csvrows = csv.reader(csvfile, delimiter=',', quotechar='"')
        line_count = 0
        count = 0
        for row in csvrows:
            if line_count == 0:
                line_count += 1
            else:
                filename = row[11].lower() + '_' + row[16].replace('.', '').lower() + '_' + row[13] + '(' + row[19] + ')'
                profile_url = row[3]
                firm_url = row[14]

                try:
                    if not profile_url:
                        print("This person doesn't have profile image.")
                    else:
                        file_type = '.png'
                        if '.jpg' in profile_url:
                            file_type = '.jpg'
                        profile_url = urllib.parse.quote(profile_url, safe=':/')
                        urllib.request.urlretrieve(profile_url, filename + file_type)

                    if not firm_url:
                        print("This person doesn't have law firm image.")
                    else:
                        if '.jpg' in firm_url:
                            file_type = '.jpg'
                        elif '.png' in firm_url:
                            file_type = '.png'
                        firm_url = urllib.parse.quote(firm_url, safe=':/')
                        urllib.request.urlretrieve(firm_url, filename + '_firm' + file_type)
                    count += 1

                except:
                    print('ERROR WHILE PARSING IMAGE URL !!!')

                print(count)


if __name__ == "__main__":
    main()
