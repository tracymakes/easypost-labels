import settings
import argparse
import csv
import easypost
import os
import requests
import shutil
import time

from slugify import slugify

"""
Program to take a CSV of book orders and use the EasyPost API to buy and create
labels for each order.

NOTE: There are custom values here for Hello Web App that should be overridden
if you're using this for your own items.
"""

def import_csv(path='orders.csv'):
    csv_rows = []

    # import csv
    print "Importing CSV."
    with open(path, 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            csv_rows.append(row)

    # remove the first row as it's just header information
    csv_rows.pop(0)
    return csv_rows


def setup_customs(country, type):
    if type == "1":
        customs_item1 = easypost.CustomsItem.create(**settings.HWA1_DESCRIPTION)
    elif type == "2":
        customs_item1 = easypost.CustomsItem.create(**settings.HWA2_DESCRIPTION)
    elif type == "12":
        customs_item1 = easypost.CustomsItem.create(**settings.DOUBLE_ITEM_DESCRIPTION)

    eel_pfc = 'NOEEI 30.37(a)'
    if country == 'CA':
        # Canada
        eel_pfc = 'NOEEI 30.36'

    customs_info = easypost.CustomsInfo.create(
        eel_pfc = eel_pfc,
        customs_certify = True,
        customs_signer = 'Tracy Osborn',
        contents_type = 'merchandise',
        customs_items = [customs_item1,]
    )

    return customs_info


def setup_shipment(row, from_address, days_advance, type, customs=None):
    #print "Setting up the shipment."

    to_address = easypost.Address.create(
      name = row[0],
      street1 = row[1],
      street2 = row[2],
      city = row[3],
      state = row[4],
      zip = row[5],
      country = row[6],
    )

    if not row[7]:
        raise ValueError("Missing package type.")

    if type == "1":
        weight = "10"
    elif type == "2":
        weight = "13"
    elif type == "12":
        weight = "21"

    parcel = easypost.Parcel.create(
      predefined_package = 'Parcel',
      weight = weight,
    )

    shipment = easypost.Shipment.create(
      to_address = to_address,
      from_address = from_address,
      parcel = parcel,
      customs_info = customs,
      options = {
          'special_rates_eligibility':'USPS.MEDIAMAIL',
          'date_advance': days_advance,
      }
    )

    return shipment


def buy_postage(shipment, speed="normal"):
    """
    Can choose from several different shipping rates:
    - normal (Media Mail for US, first for International)
    - premium (Priority for US, not offered for International)
    - urgent (Overnight for US, not offered for International)
    """

    country = shipment['from_address'].get('country', 'US')
    rate = None
    if country == 'US':
        if speed == "premium":
            rate = shipment.lowest_rate(carriers=['USPS'], services=['Priority'])
        elif speed == "urgent":
            rate = shipment.lowest_rate(carriers=['USPS'], services=['Express'])
        else:
            rate = shipment.lowest_rate(carriers=['USPS'],)
    else:
        rate = shipment.lowest_rate()

    shipment.buy(rate=rate)
    #print "Speed: %s" % shipment.rate
    return shipment


def export_postage(label_url, file_name):
    url = label_url

    response = requests.get(url, stream=True)
    with open(file_name, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response


def main():
    # Will default to creating labels for today that will need to be shipped
    # within 24 hours. Add the days argument to change the date.t 
    parser = argparse.ArgumentParser(description='Create shipping labels from EasyPost.com.')
    parser.add_argument('--days', dest='days', metavar='N', type=int, help='Days from now that you want to ship the label(s). Default is today.', default=0)
    parser.add_argument('--domestic', dest='domestic', metavar='COUNTRY', type=str, help='2-letter country code of origin that is considered domestic. Default: US', default='US')
    parser.add_argument('orders', metavar='CSV')

    args = parser.parse_args()
    days_advance = args.days

    easypost.api_key = os.getenv('EASYPOST_API_KEY')
    if not easypost.api_key:
        raise ValueError("Missing EASYPOST_API_KEY env var.")

    date = time.strftime("%Y-%m-%d")
    from_address = easypost.Address.create(**settings.FROM_ADDRESS)

    # import csv
    csv_rows = import_csv(args.orders)

    # create folder for labels
    directory = "labels/%s" % date
    if not os.path.exists(directory):
        os.makedirs(directory)

    # set up logging file
    file = open(os.path.join(directory, "log.csv"), "a")

    # track the total cost
    total_cost = 0

    for i, row in enumerate(csv_rows):
        print i, row
        customs = []
        name = row[0]

        # set file name (so we can check whether it's already been created)
        file_name = "%s/img-%s.png" % (directory, slugify(name))
        if os.path.isfile(file_name):
            print "Label exists!"
            continue

        # set variables for speed, location, and which books
        type = row[7]
        speed = row[8]
        country = row[6]

        # set up customs for international
        customs = setup_customs(country, type)

        # set up the shipment
        shipment = setup_shipment(row, from_address, days_advance, type, customs)

        # buy the postage
        shipment = buy_postage(shipment, speed)

        # print label
        label_url = shipment["postage_label"]["label_url"]
        selected_carrier = shipment["selected_rate"]["carrier"]
        selected_service = shipment["selected_rate"]["service"]
        selected_rate = shipment["selected_rate"]["rate"]
        tracking_code = shipment["tracker"]["tracking_code"]

        print "Label URL: %s" % label_url
        print "Selected rate: %s %s $%s" % (selected_carrier, selected_service, selected_rate)
        print "Tracking code: %s" % tracking_code

        #print "Exporting image."
        export_postage(label_url, file_name)

        file.write(u"%s,%s,$%s,%s,%s\n" % (name.decode('ascii', 'ignore'), tracking_code, label_url, selected_service, selected_rate))
        total_cost += float(selected_rate)
        print "Total cost so far: $%s" % total_cost
        print "------"

    file.write("$%s" % total_cost)
    file.close()


if __name__ == "__main__":
    main()
