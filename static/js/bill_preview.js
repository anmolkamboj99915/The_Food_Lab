(function () {
    const itemsField = document.getElementById('id_items_ordered');
    const billAmountField = document.getElementById('id_bill_amount');
    const gstField = document.getElementById('id_gst');
    const discountField = document.getElementById('id_discount');

    if (!itemsField || !document.querySelector('[data-bill-preview]')) {
        return;
    }

    const setText = function (key, value) {
        const element = document.querySelector('[data-bill-preview="' + key + '"]');
        if (element) {
            element.textContent = value;
        }
    };

    const toNumber = function (value) {
        const parsed = Number.parseFloat(String(value || '').replace(/,/g, ''));
        return Number.isFinite(parsed) ? parsed : 0;
    };

    const money = function (value) {
        return 'Rs. ' + value.toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    };

    const calculateItems = function () {
        return itemsField.value.split(/\r?\n/).reduce(function (summary, rawLine) {
            const line = rawLine.trim();
            if (!line) {
                return summary;
            }

            const parts = line.split(',').map(function (part) {
                return part.trim();
            });
            if (parts.length !== 3) {
                summary.invalid += 1;
                return summary;
            }

            const quantity = toNumber(parts[1]);
            const price = toNumber(parts[2]);
            if (!parts[0] || quantity <= 0 || price < 0) {
                summary.invalid += 1;
                return summary;
            }

            summary.count += 1;
            summary.subtotal += quantity * price;
            return summary;
        }, { count: 0, invalid: 0, subtotal: 0 });
    };

    const updatePreview = function () {
        const itemSummary = calculateItems();
        const manualSubtotal = toNumber(billAmountField && billAmountField.value);
        const subtotal = manualSubtotal > 0 ? manualSubtotal : itemSummary.subtotal;
        const gstPercent = toNumber(gstField && gstField.value);
        const discount = toNumber(discountField && discountField.value);
        const gst = subtotal * gstPercent / 100;
        const grand = Math.max(subtotal + gst - discount, 0);

        setText('items', String(itemSummary.count));
        setText('subtotal', money(subtotal));
        setText('gst', money(gst));
        setText('discount', money(discount));
        setText('grand', money(grand));

        if (itemSummary.invalid) {
            setText('hint', itemSummary.invalid + ' item line needs format: name, quantity, price.');
        } else if (itemSummary.count) {
            setText('hint', 'Ready to save and send this bill.');
        } else {
            setText('hint', 'Start entering items to preview totals.');
        }
    };

    [itemsField, billAmountField, gstField, discountField].forEach(function (field) {
        if (field) {
            field.addEventListener('input', updatePreview);
        }
    });

    updatePreview();
}());
