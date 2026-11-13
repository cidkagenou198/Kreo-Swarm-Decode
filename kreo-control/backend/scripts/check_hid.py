import hid

devs = hid.enumerate()
kreo_devs = [d for d in devs if (d['vendor_id'], d['product_id']) in [(0x3554, 0xFA09), (0x258A, 0x010C)]]
print(f"Found {len(kreo_devs)} Kreo device interfaces:")
for d in kreo_devs:
    print(f"  VID={hex(d['vendor_id'])} PID={hex(d['product_id'])} Interface={d['interface_number']} UsagePage={hex(d['usage_page'])} Usage={hex(d['usage'])}")

