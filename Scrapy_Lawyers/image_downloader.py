import csv
import requests


def main():
    with open('result.csv') as csvfile:
        csvrows = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in csvrows:
            filename = row[0]
            url = row[1]
            print(url)
            result = requests.get(url, stream=True)
            if result.status_code == 200:
                image = result.raw.read()
                open(filename, "wb").write(image)


if __name__ == "__main__":
    main()
