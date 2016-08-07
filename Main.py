import requests
from Tkinter import *
from threading import Thread


class StockCheckerApp(object):
    def __init__(self, master, width=1200, height=1200):
        self.sku = ''
        self.client_id = ''

        # set dimensions
        master.geometry('{}x{}'.format(width, height))

        # set title of window
        master.wm_title('Adidas Stock Checker')

        self.left_frame = Frame(master, width=width/2, height=height)
        self.left_frame.pack(side=LEFT)

        self.right_frame = Frame(master, width=width/2, height=height)
        self.right_frame.pack(side=RIGHT)

        self.sku_input = Entry(self.left_frame)
        self.sku_input.insert(0, 'SKU Here')
        self.sku_input.pack(anchor='w')

        self.client_id_input = Entry(self.left_frame)
        self.client_id_input.insert(0, 'Client ID Here')
        self.client_id_input.pack(anchor='w')

        self.region_input = Entry(self.left_frame)
        self.region_input.insert(0, 'Region Here')
        self.region_input.pack(anchor='w')

        self.submit_btn = Button(self.left_frame, text='Display Stock', command=self.get_stock)
        self.submit_btn.pack(anchor='w')

        self.status_entry = Entry(self.left_frame)
        self.update_status('Awaiting SKU...')

        self.quit_btn = Button(self.left_frame, text='Quit', command=self.left_frame.quit)
        self.quit_btn.pack(anchor='w')

    def update_status(self, status):
        self.status_entry.configure(state=NORMAL)
        self.status_entry.delete(0, 'end')
        self.status_entry.insert(0, status)
        self.status_entry.configure(state='readonly')
        self.status_entry.pack()

    def get_stock(self):
        self.sku = self.sku_input.get().strip()
        self.client_id = self.client_id_input.get().strip()

        self.update_status('Retrieving {}...'.format(self.sku))

        region = self.region_input.get()

        thread = Thread(name=self.sku+'_'+region, target=self.check_stock, args=[region])
        thread.daemon = True
        thread.start()

    def check_stock(self, region):
        region = region.upper()
        given_sku = self.sku
        is_main_sku = '_' not in self.sku

        s = requests.Session()
        s.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'

        base = 'http://production-us-adidasgroup.demandware.net/s/adidas-{}/dw/shop/v15_6/products/'.format(region)
        if region != 'US' and region != 'CA' and region != 'MX':
            base = base.replace('-us', '-store')

        url = base+self.sku

        params = {
            'client_id': self.client_id,
            'expand': 'availability,variations,prices'
        }

        res = s.get(url, params=params)
        json_dict = res.json()

        if is_main_sku and 'fault' in json_dict:
            err_msg = json_dict['fault']['message']
            self.display_stock(err_msg)
            self.update_status('Error')
            return

        qty = json_dict['inventory']['ats']
        stock = list()

        if is_main_sku:
            variants = json_dict['variants']
            for variant in variants:
                self.sku = variant['product_id']

                entry = {self.sku: self.check_stock(region)}
                stock.append(entry)

            total = 0
            for entry in stock:
                sku = list(entry)[0]
                total += entry[sku]
            stock.append({'Total': total})

            self.update_status('Retrieved '+given_sku)

            self.display_stock(stock, json_dict['name'])
        else:
            return qty

    def display_stock(self, stock_entries, product_name=''):
        # clear frame of any previous entries
        for child in self.right_frame.winfo_children():
            child.destroy()

        if isinstance(stock_entries, list):
            name_label_display = Entry(self.right_frame)
            name_label_display.insert(0, 'Name')
            name_label_display.configure(state='readonly')
            name_label_display.grid(row=0, column=0)

            name_display = Entry(self.right_frame)
            name_display.insert(0, product_name)
            name_display.configure(state='readonly')
            name_display.grid(row=0, column=1)

            for stock_entry in stock_entries:
                sku = list(stock_entry)[0]

                i = stock_entries.index(stock_entry)+1

                sku_display = Entry(self.right_frame)
                sku_display.insert(0, sku)
                sku_display.configure(state='readonly')
                sku_display.grid(row=i, column=0)

                qty_display = Entry(self.right_frame)
                qty_display.insert(0, str(stock_entry[sku]))
                qty_display.configure(state='readonly')
                qty_display.grid(row=i, column=1)
        else:  # the stock variable is an error
            err_display = Entry(self.right_frame)
            err_display.insert(0, stock_entries)
            err_display.configure(state='readonly')
            err_display.grid(row=0, column=0)


root = Tk()
# root.resizable(width=False, height=False)

app = StockCheckerApp(root)

root.mainloop()

