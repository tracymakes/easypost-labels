import easypost
import csv
import requests
import shutil

from slugify import slugify

easypost.api_key = 'hLbx0e4o1Y5khc3t6QMeUw'

fromAddress = easypost.Address.create(
  company = 'Tracy Osborn',
  street1 = '1547 Montellano Drive',
  city = 'San Jose',
  state = 'CA',
  zip = '95120',
  phone = '425-998-7229',
)


def import_csv():
    us_csv_rows, int_csv_rows = [], []

    # import domestic csv
    print "Importing domestic CSV."
    with open('us.csv', 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            us_csv_rows.append(row)

    # import international csv
    print "Importing international CSV."
    with open('int.csv', 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            int_csv_rows.append(row)

    # remove the first row as it's just header information
    us_csv_rows.pop(0)
    int_csv_rows.pop(0)
    return us_csv_rows, int_csv_rows


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
    with open('img-%s.png' % name, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response



us_csv_rows, int_csv_rows = import_csv()
for row in int_csv_rows:
    canada = False
    if row[6] == "CA":
        canada = True

    customs = setup_customs(canada)
    shipment = setup_shipment(row, customs)
    shipment = buy_postage(shipment)

    print shipment
    label_url = shipment["postage_label"]["label_url"]
    selected_rate = shipment["selected_rate"]["rate"]

    print "Label URL: " + label_url
    print "Selected rate: $" + selected_rate

    print "Exporting image:"
    export_postage(label_url, row[0])
