import csv
import argparse


def getTileCords(rows):
    # When we have tile input process here, for now we fake.
    tile_size = 768

    # square with four tiles
    tile_cords = dict()

    for row in rows:
        index1 = row[1].find('.')
        row[1] = row[1][0:index1]
        index2 = row[2].find('.')
        row[2] = row[2][0:index2]
        index3 = row[3].find('.')
        row[3] = row[3][0:index3]
        index4 = row[4].find('.')
        row[4] = row[4][0:index4]

    counter = 0
    for row in rows:
        if float(row[5]) >= 0.5:
            tile_cord0 = dict()
            tile_cord0['x0'] = int(row[1])
            tile_cord0['x1'] = int(row[1]) + int(row[3])
            tile_cord0['y0'] = int(row[2])
            tile_cord0['y1'] = int(row[2]) + int(row[4])
            tile_cord0['tv'] = row[0]
            tile_cord0['confidence'] = float(row[5])
            if float(row[5]) >= 0.5 and float(row[5]) < 0.75:
                tile_cord0['color'] = 'yellow'
            elif float(row[5]) >= 0.75:
                tile_cord0['color'] = 'red'
            else:
                tile_cord0['color'] = 'green'
            tile_cords[counter] = tile_cord0
            counter = counter + 1

    # print(tile_cords)
    calculated_tile_size = tile_cords[0]['x1'] - tile_cords[0]['x0']

    # for i, tile in tile_cords.items:
    #   calculated_tile_size[i] = tile_cords[i]['x1'] - tile_cords[i]['x0']

    max_x = 0
    max_y = 0

    for tile_id, coord in tile_cords.items():
        if coord['x1'] > max_x:
            max_x = coord['x1']
        if coord['y1'] > max_y:
            max_y = coord['y1']

    return calculated_tile_size, max_x, max_y, tile_cords


def getLines(calculated_tile_size, max_x, max_y, tile_cords):
    x_line_keys = []

    x_min = 0
    counter = 1
    for y in range(0, max_y + calculated_tile_size, calculated_tile_size):
        for x in range(0, max_x + calculated_tile_size, calculated_tile_size):

            if (x > 0):
                xline = dict()
                xline['x0'] = x_min
                xline['x1'] = x
                xline['y'] = y

                counter = counter + 1
                x_line_keys.append(xline)
            x_min = x
        x_min = 0

    cx_lines = []

    for xline in x_line_keys:
        match_coords = []
        for coord in x_line_keys:
            # print('we are here')
            # print(type(xline['x0']))
            # print(coord['x0'])
            # print(xline['x1'])
            # print(coord['x1'])
            # print(xline['y'])
            # print(coord['y0'])
            if (xline['x0'] == coord['x0']) and (xline['x1'] == coord['x1']) and (xline['y'] == coord['y']):
                print('Coord: ' + str(coord))
                match_coords.append(coord['color'])
                print('Match Coords: ' + str(match_coords))
            # if (xline['x0'] == coord['x0']) and (xline['x1'] == coord['x1']) and (xline['y'] == coord['y1']):
            #   print('coord y1: ' + coord)
            #   match_coords.append(coord['color'])
            #   print('match coords y1: ' + match_coords)

        # print(coord)
        if (len(match_coords) > 0):
            if (len(match_coords) == 1):
                xline['color'] = match_coords[0]
                cx_lines.append(xline)
                print(cx_lines)
            else:
                if match_coords[0] not in match_coords[1]:
                    xline['color'] = match_coords[0] + '-' + match_coords[1]
                    cx_lines.append(xline)

    print(cx_lines)

    return cx_lines


def run_script():

        rows = []
        with open('new_coords.csv', newline='') as f:
            csvreader = csv.reader(f)
            header = next(csvreader)
            for row in csvreader:
                rows.append(row)



        calculated_tile_size, max_x, max_y, tile_cords = getTileCords(rows)

        cx_lines = getLines(calculated_tile_size, max_x, max_y, tile_cords)


if __name__ == "__main__":
    run_script()