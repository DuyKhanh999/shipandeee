from flask import Flask, request, render_template, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Thay đổi thành một giá trị bảo mật và duy nhất của bạn

# Đọc dữ liệu từ file Excel
import pandas as pd
df = pd.read_excel('menu.xlsx')

# Route chính
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if request.form.get('action') == 'reset':
            # Xóa thông tin khách hàng và các mục đã chọn
            session.pop('customer_info', None)
            session.pop('invoice', None)
            return redirect(url_for('index'))

        # Lưu thông tin khách hàng vào session
        session['customer_info'] = {
            'customer': request.form.get('customer'),
            'phone': request.form.get('phone'),
            'address': request.form.get('address')
        }

        # Xử lý danh sách món ăn
        items = request.form.getlist('item')
        quantities = request.form.getlist('quantity')
        ship = int(request.form.get('ship', 0))

        selected_items = []
        for i, item in enumerate(items):
            item_price = df[df['Tên món'] == item]['Giá'].values
            if item_price.size > 0:
                price = int(item_price[0])
                quantity = int(quantities[i])
                selected_items.append({
                    'Tên món': item,
                    'Số lượng': quantity,
                    'Giá': price
                })

        total = sum(item['Giá'] * item['Số lượng'] for item in selected_items) + ship

        # Chuyển đổi các giá trị thành kiểu int để tránh lỗi JSON serializable
        invoice_data = {
            'customer_info': session.get('customer_info', {}),
            'selected_items': selected_items,
            'ship': int(ship),
            'total': int(total)
        }

        # Lưu hóa đơn vào session
        session['invoice'] = invoice_data

        return redirect(url_for('invoice'))

    # Khi tải lại trang, xóa thông tin khách hàng
    session.pop('customer_info', None)
    customer_info = {}
    
    total = 0
    selected_items = []

    return render_template('index.html', menu=df.to_dict('records'), total=total, selected_items=selected_items, customer_info=customer_info)

@app.route('/suggest')
def suggest():
    query = request.args.get('q', '')
    suggestions = df[df['Tên món'].str.contains(query, case=False, na=False)]
    return jsonify(suggestions.to_dict(orient='records'))

@app.route('/invoice')
def invoice():
    invoice_data = session.get('invoice', {})
    if not invoice_data:
        return redirect(url_for('index'))

    customer_info = invoice_data.get('customer_info', {})
    selected_items = invoice_data.get('selected_items', [])
    ship = invoice_data.get('ship', 0)
    total = invoice_data.get('total', 0)

    return render_template('invoice.html', customer_info=customer_info, selected_items=selected_items, ship=ship, total=total)

if __name__ == '__main__':
    app.run(debug=True)
