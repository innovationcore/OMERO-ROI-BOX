import omero.scripts as scripts
from omero.gateway import BlitzGateway
from omero.rtypes import rlong, rint, rstring, robject, unwrap, rdouble
from omero.model import RectangleI, EllipseI, LineI, PolygonI, PolylineI, \
    MaskI, LabelI, PointI, RoiI
from math import sqrt, pi
import re
import csv
import argparse


# We have a helper function for creating an ROI and linking it to new shapes
def create_roi(img, shapes, updateService):
    # create an ROI, link it to Image
    roi = RoiI()
    # use the omero.model.ImageI that underlies the 'image' wrapper
    roi.setImage(img._obj)
    for shape in shapes:
        roi.addShape(shape)
    # Save the ROI (saves any linked shapes too)
    return updateService.saveAndReturnObject(roi)


# Another helper for generating the color integers for shapes
def rgba_to_int(red, green, blue, alpha=255):
    """ Return the color as an Integer in RGBA encoding """
    r = red << 24
    g = green << 16
    b = blue << 8
    a = alpha
    rgba_int = r + g + b + a
    if (rgba_int > (2 ** 31 - 1)):  # convert to signed 32-bit int
        rgba_int = rgba_int - 2 ** 32
    return rgba_int


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
    """The main entry point of the script, as called by the client."""
    data_types = [rstring('Dataset'), rstring('Image')]

    # Here are some variables you can ask the user before processing
    client = scripts.client(
        'Batch_ROI_Export.py',
        """Annotate image using ROIs for selected Images.""",

        # scripts.String(
        #     "Data_Type", optional=False, grouping="1",
        #     description="The data you want to work with.", values=data_types,
        #     default="Image"),

        scripts.List(
            "IDs", optional=False, grouping="2",
            description="List of Dataset IDs or Image IDs").ofType(rlong(0)),

        # scripts.List(
        #     "Channels", grouping="3", default=[0, 1, 2],
        #     description="Indices of Channels to measure intensity."
        # ).ofType(rint(0)),

        # scripts.Bool(
        #     "Export_All_Planes", grouping="4",
        #     description=("Export all Z and T planes for shapes "
        #                  "where Z and T are not set?"),
        #     default=False),

        # scripts.String(
        #     "File_Name", grouping="5", default=DEFAULT_FILE_NAME,
        #     description="Name of the exported CSV file"),

        authors=["William Moore", "OME Team"],
        institutions=["University of Dundee"],
        contact="ome-users@lists.openmicroscopy.org.uk",
    )

    try:
        conn = BlitzGateway(client_obj=client)

        script_params = client.getInputs(unwrap=True)

        # First we load our image and pick some parameters for shapes
        x = 50
        y = 200
        width = 10000
        height = 5000
        image = conn.getObject("Image", script_params["IDs"][0])
        z = 0
        t = 0

        rows = []
        with open('/opt/scripts/new_coords.csv', newline='') as f:
            csvreader = csv.reader(f)
            header = next(csvreader)
            for row in csvreader:
                rows.append(row)

        # create a rectangle shape (added to ROI below)
        # client.setOutput("Message", rstring("Adding a rectangle at theZ: "+str(z)+", theT: "+str(t)+", X: "+str(x)+", Y: "+str(y)+", width: "+str(width)+", height: "+str(height)))
        client.setOutput("Message", rstring("Finished Annotating"))

        calculated_tile_size, max_x, max_y, tile_cords = getTileCords(rows)

        cx_lines = getLines(calculated_tile_size, max_x, max_y, tile_cords)

        # print(cx_lines)

        # create an Ellipse shape (added to ROI below)
        # ellipse = EllipseI()
        # ellipse.x = rdouble(y)
        # ellipse.y = rdouble(x)
        # ellipse.radiusX = rdouble(width)
        # ellipse.radiusY = rdouble(height)
        # ellipse.theZ = rint(z)
        # ellipse.theT = rint(t)
        # ellipse.textValue = rstring("test-Ellipse")

        # Create an ROI containing 2 shapes on same plane
        # NB: OMERO.insight client doesn't support display
        # of multiple shapes on a single plane.
        # Therefore the ellipse is removed later (see below)

        # log("script_params:")
        # log(script_params)

        # # call the main script
        # result = batch_roi_export(conn, script_params)

        # # Return message and file_annotation to client
        # if result is None:
        #     message = "No images found"
        # else:
        #     file_ann, message = result
        #     if file_ann is not None:
        #         client.setOutput("File_Annotation", robject(file_ann._obj))

        # client.setOutput("Message", rstring(message))

    # roi_service = conn.getRoiService()
    # result = roi_service.findByImage(imageId, None)
    # roi_ids = [roi.id.val for roi in result.rois]
    # conn.deleteObjects("Roi", roi_ids)

    finally:
        client.closeSession()


if __name__ == "__main__":
    run_script()