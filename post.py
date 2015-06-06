import argparse
import csv
import easypost
import os
import requests
import shutil
import time

from slugify import slugify


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


def setup_shipment(row, from_address, days_advance, customs=None):
    print "Setting up the shipment."

    to_address = easypost.Address.create(
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


def buy_postage(shipment):
    print "Buying lowest rate from USPS."
    shipment.buy(rate=shipment.lowest_rate(carriers=['USPS'],))

    return shipment


def export_postage(label_url, file_name):
    url = label_url

    response = requests.get(url, stream=True)
    with open(file_name, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response


def main():
    parser = argparse.ArgumentParser(description='Create shipping labels from EasyPost.com.')
    parser.add_argument('--days', dest='days', metavar='N', type=int, help='Days from now that you want to ship the label(s). Default is today.', default=0)

    args = parser.parse_args()
    days_advance = args.days

    easypost.api_key = os.getenv('EASYPOST_API_KEY')
    if not easypost.api_key:
        raise ValueError("Missing EASYPOST_API_KEY env var.")

    date = time.strftime("%Y-%m-%d")
    from_address = easypost.Address.create(
      company = 'Tracy Osborn',
      street1 = '1547 Montellano Drive',
      city = 'San Jose',
      state = 'CA',
      zip = '95120',
      phone = '425-998-7229',
    )

    # import csv
    csv_rows = import_csv()

    # create folder for labels
    directory = date
    if not os.path.exists(directory):
        os.makedirs(directory)

    # set up logging file
    file = open(os.path.join(directory, "log.csv"), "a")

    # track the total cost
    total_cost = 0

    for row in csv_rows:
        domestic = False
        canada = False
        customs = []
        name = row[0]

        # set file name (so we can check whether it's already been created)
        file_name = "%s/img-%s.png" % (directory, slugify(name))
        if os.path.isfile(file_name):
            print "Label exists!"
            continue

        print "Country: " + row[6]
        if row[6] == "US":
            domestic = True
        elif row[6] == "CA":
            canada = True

        if not domestic:
            customs = setup_customs(canada)

        shipment = setup_shipment(row, from_address, days_advance, customs)
        shipment = buy_postage(shipment)

        #print shipment
        label_url = shipment["postage_label"]["label_url"]
        selected_rate = shipment["selected_rate"]["rate"]
        tracking_code = shipment["tracker"]["tracking_code"]

        print "Label URL: " + label_url
        print "Selected rate: $" + selected_rate
        print "Tracking code: " + tracking_code

        print "Exporting image."
        export_postage(label_url, file_name)

        file.write(u"%s,%s,$%s\n" % (name.decode('ascii', 'ignore'), tracking_code, selected_rate))
        total_cost += float(selected_rate)

    file.write("$%s" % total_cost)
    file.close()



if __name__ == "__main__":
    main()
