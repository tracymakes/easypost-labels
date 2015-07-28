# Create a settings_local.py and overwrite these settings
# Refer to the EasyPost docs for info

ITEM_DESCRIPTION = {
    'description': 'My Item',
    'quantity': 1,
    'value': 20,
    'weight': 10,
    'hs_tariff_number': 490199,
    'origin_country': 'US'
}

FROM_ADDRESS = {
    'company': "My Corp",
    'street1': "123 My Street",
    'city': 'My City',
    'state': 'CA',
    'zip': '90210',
    'phone': '800-555-1234',
}

try:
    # Import local settings override if exists.
    from settings_local import *
except ImportError:
    pass
