import csv

# 从文件读取
with open('screw_log.csv', "r") as f:
    reader = csv.reader((line.replace('\0', '') for line in f))

    t = 0
    s = 0
    try:
        for line in reader:
            print('...............', line)

            d = line[0]
            print('/////////////', d)
            if d.isdigit():
                if int(d) >= t:
                    t = int(d)
                    print('tttttttttttt', t)
            else:
                s += t
                t = 0
                print('============', s)
    except Exception as e:
        print('eeeeeeeeeeee', e)
        pass
    print('total cycle is: ', s)

