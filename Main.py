import requests
from Tkinter import *  # if you are using python 3+, change this line to "from tkinter import *"
from threading import Thread
import time


class StockCheckerApp(object):
    def __init__(self, master, width=1200, height=1200):
        self.sku = ''
        self.client_id = ''
        self.cycle = 1

        # set dimensions
        master.geometry('{}x{}'.format(width, height))

        # set title of window
        master.wm_title('Adidas Stock Checker')

        self.left_frame = Frame(master, width=width/2, height=height)
        self.left_frame.pack(side=LEFT)

        self.right_frame = Frame(master, width=width/2, height=height)
        self.right_frame.pack(side=RIGHT)

        # sku label and input
        self.sku_label = Label(self.left_frame, text='Enter SKU:')
        self.sku_label.pack(anchor='w')
        self.sku_input = Entry(self.left_frame)
        self.sku_input.insert(0, 'SKU Here')
        self.sku_input.pack(anchor='w')

        add_space(self.left_frame)

        # client id label and input
        self.client_id_label = Label(self.left_frame, text='Enter Client ID:')
        self.client_id_label.pack(anchor='w')
        self.client_id_input = Entry(self.left_frame)
        self.client_id_input.insert(0, 'Client ID Here')
        self.client_id_input.pack(anchor='w')

        add_space(self.left_frame)

        # region label and input
        self.region_label = Label(self.left_frame, text='Enter region:')
        self.region_label.pack(anchor='w')
        self.region_input = Entry(self.left_frame)
        self.region_input.insert(0, 'Region Here')
        self.region_input.pack(anchor='w')

        add_space(self.left_frame)

        """ START OF REFRESH MODE VARIABLES """

        # refresh checkbox
        self.refresh_var = BooleanVar()
        self.refresh_checkbox = Checkbutton(self.left_frame, text='Refresh Mode', variable=self.refresh_var)
        self.refresh_checkbox.bind("<Button-1>", self.update_refresh_mode)
        self.refresh_checkbox.pack(anchor='w')

        # refresh amount input and label
        self.refresh_amt_label = Label(self.left_frame, text='Enter Refresh Amount:')
        self.refresh_amt_label.pack(anchor='w')
        self.refresh_amt_input = Entry(self.left_frame)
        self.refresh_amt_input.insert(0, 'Refresh Amount Here')
        self.refresh_amt_input.pack(anchor='w')

        # refresh delay input and label
        self.refresh_dly_label = Label(self.left_frame, text='Enter Refresh Delay (Seconds):')
        self.refresh_dly_label.pack(anchor='w')
        self.refresh_dly_input = Entry(self.left_frame)
        self.refresh_dly_input.insert(0, 'Refresh Delay Here')
        self.refresh_dly_input.pack(anchor='w')

        """  END OF REFRESH MODE VARIABLES  """
        self.disable_refresh()

        add_space(self.left_frame)

        self.submit_btn = Button(self.left_frame, text='Display Stock', command=self.get_stock)
        self.submit_btn.pack(anchor='w')

        add_space(self.left_frame)
        add_space(self.left_frame)
        add_space(self.left_frame)

        self.status = Label(self.left_frame)
        self.status.pack(anchor='w')
        self.update_status('Awaiting SKU...')

        self.quit_btn = Button(self.left_frame, text='Quit', command=master.quit)
        self.quit_btn.pack(anchor='w')

    def update_refresh_mode(self, event=''):
        # you must take the opposite since the function is called
        # before the change of the checkbox
        active = not self.refresh_var.get()

        if active:
            self.enable_refresh()
        else:
            self.disable_refresh()

    def disable_refresh(self):
        self.refresh_amt_label.configure(state="disabled")
        self.refresh_amt_input.configure(state="disabled")
        self.refresh_dly_label.configure(state="disabled")
        self.refresh_dly_input.configure(state="disabled")

    def enable_refresh(self):
        self.refresh_amt_label.configure(state="normal")
        self.refresh_amt_input.configure(state="normal")
        self.refresh_dly_label.configure(state="normal")
        self.refresh_dly_input.configure(state="normal")

    def update_status(self, status):
        self.status['text'] = 'Status: '+status

    def get_stock(self):
        self.sku = self.sku_input.get().strip()
        self.client_id = self.client_id_input.get().strip()
        self.cycle = 1

        region = self.region_input.get()

        if self.refresh_var.get():
            validity = self.refresh_is_valid()
            if not validity[0]:
                self.update_status(validity[1])
                self.enable_submit()
                return
            else:
                amt = int(self.refresh_amt_input.get())
                dly = float(self.refresh_dly_input.get())

                if amt <= 0:
                    self.update_status('Please enter a non-zero/negative amount.')
                    return
                if dly < 0:
                    self.update_status('Please enter a non-negative delay.')
                    return
        else:
            amt = 1
            dly = 1

        thread = Thread(name=self.sku+'_'+region, target=self.check_stock, args=[region, amt, dly])
        thread.daemon = True
        thread.start()

        self.disable_submit()

    def check_stock(self, region, refresh=1, delay=1):
        self.update_status('Cycle {} retrieving {}...'.format(self.cycle, self.sku))

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
            self.update_status(err_msg)
            return

        qty = json_dict['inventory']['ats']
        stock = list()

        if is_main_sku:
            variants = json_dict['variants']
            variant_attrs = json_dict['variation_attributes'][0]['values']
            for variant in variants:
                index = variants.index(variant)
                self.sku = variant['product_id']

                entry_name = self.sku+' ({})'.format(variant_attrs[index]['name'])

                entry = {entry_name: self.check_stock(region)}
                stock.append(entry)

            total = 0
            for entry in stock:
                sku = list(entry)[0]
                total += entry[sku]
            stock.append({'Total': total})

            self.update_status('Cycle {} retrieved {}'.format(self.cycle, given_sku))

            self.display_stock(stock, json_dict['name'])

            self.sku = given_sku
            if refresh > 1:
                self.cycle += 1
                time.sleep(delay)
                self.check_stock(region, refresh-1)
            else:
                self.enable_submit()
        else:
            return qty

    def display_stock(self, stock_entries, product_name=''):
        # clear frame of any previous entries
        for child in self.right_frame.winfo_children():
            child.destroy()

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

    def refresh_is_valid(self):
        err_msg = ''
        valid = True

        try:
            float(self.refresh_dly_input.get())
        except ValueError:
            err_msg = 'Please input valid refresh delay'
            valid = False

        try:
            int(self.refresh_amt_input.get())
        except ValueError:
            err_msg = 'Please input valid refresh amount'
            valid = False

        return valid, err_msg

    def disable_submit(self):
        self.submit_btn.configure(state='disabled')

    def enable_submit(self):
        self.submit_btn.configure(state='normal')


def add_space(frame):
    space = Label(frame)
    space.pack()


root = Tk()
# root.resizable(width=False, height=False)

app = StockCheckerApp(root)

root.mainloop()

