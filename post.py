import csv
import easypost
import logging
import os
import requests
import shutil
import time

from slugify import slugify

easypost.api_key = 'hLbx0e4o1Y5khc3t6QMeUw'
date = time.strftime("%Y/%m/%d")
fromAddress = easypost.Address.create(
  company = 'Tracy Osborn',
  street1 = '1547 Montellano Drive',
  city = 'San Jose',
  state = 'CA',
  zip = '95120',
  phone = '425-998-7229',
)

# create folder for labels
directory = date.replace("/", "-")
if not os.path.exists(directory):
    os.makedirs(directory)

file = open("%s/newfile.txt", "w") % directory
file.write("hello world in the new file\n")
file.close()


def import_csv():
    csv_rows = []

    # import csv
    print "Importing CSV."
    with open('orders.csv', 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            csv_rows.append(row)

    # remove the first row as it's just header information
    csv_rows.pop(0)
    return csv_rows


def setup_customs(canada):
    customs_item1 = easypost.CustomsItem.create(
        description = 'Hello Web App book',
        quantity = 1,
        value = 20,
        weight = 10,
        hs_tariff_number = 490199,
        origin_country = 'US'
    )

    eel_pfc = 'NOEEI 30.37(a)'
    if canada:
        eel_pfc = 'NOEEI 30.36'

    customs_info = easypost.CustomsInfo.create(
        eel_pfc = eel_pfc,
        customs_certify = True,
        customs_signer = 'Tracy Osborn',
        contents_type = 'merchandise',
        customs_items = [customs_item1,]
    )

    return customs_info


def setup_shipment(row, customs=None):
    print "Setting up the shipment."

    toAddress = easypost.Address.create(
      name = row[0],
      street1 = row[1],
      street2 = row[2],
      city = row[3],
      state = row[4],
      zip = row[5],
      country = row[6],
    )

    parcel = easypost.Parcel.create(
      predefined_package = 'Parcel',
      weight = 10,
    )

    shipment = easypost.Shipment.create(
      to_address = toAddress,
      from_address = fromAddress,
      parcel = parcel,
      customs_info = customs,
      options = {
          'special_rates_eligibility':'USPS.MEDIAMAIL',
      }
    )

    return shipment


def buy_postage(shipment):
    print "Buying lowest rate from USPS."
    shipment.buy(rate=shipment.lowest_rate(carriers=['USPS'],))

    return shipment


def export_postage(label_url, name):
    url = label_url
    name = slugify(name)

    response = requests.get(url, stream=True)
    with open('%s/img-%s.png' % (directory, name), 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response


csv_rows = import_csv()
# TODO: Create log file exporting the tracking numbers and names of the shipments
# TODO: Investigate tracking and see whether it's included or not
# XXX: Make sure I can set the shipping date
for row in csv_rows:
    domestic = False
    canada = False
    customs = []

    print "Country: " + row[6]
    if row[6] == "US":
        domestic = True
    elif row[6] == "CA":
        canada = True

    if not domestic:
        customs = setup_customs(canada)

    shipment = setup_shipment(row, customs)
    shipment = buy_postage(shipment)

    print shipment
    label_url = shipment["postage_label"]["label_url"]
    selected_rate = shipment["selected_rate"]["rate"]
    tracking_code = shipment["tracker"]["tracking_code"]

    print "Label URL: " + label_url
    print "Selected rate: $" + selected_rate
    print "Tracking code: " + tracking_code

    print "Exporting image."
    export_postage(label_url, row[0])
