import os
from io import BytesIO
import streamlit as st
import pandas as pd
from PIL import Image

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


# ---------------------------
# Helpers
# ---------------------------
def krw(n: float) -> str:
    try:
        return f"{int(round(n)):,} KRW"
    except Exception:
        return "0 KRW"


def build_invoice_pdf(data: dict) -> bytes:
    """
    PDF에는 인보이스 항목만 출력 (Breakdown/세부사항 미출력)
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    # ===== Header (Logo + Company Name) =====
    logo_path = os.path.join(os.path.dirname(__file__), "Logo_Main_Full_Color_2.jpg")

    try:
        img = Image.open(logo_path).convert("RGB")  # JPG 호환 문제 방지
        c.drawInlineImage(img, 60, height - 120, width=170, height=50)
    except Exception:
        pass

    c.setFont("Helvetica-Bold", 18)
    c.drawString(250, height - 85, "TOUR STORY")

    y = height - 125
    c.setLineWidth(0.5)
    c.line(60, y, width - 60, y)
    y -= 28

    c.setFont("Helvetica", 10)

    # Top row
    c.drawString(60, y, "Invoice No:")
    c.drawString(140, y, f"[{data['invoice_no']}]")
    c.drawString(width - 220, y, "Date:")
    c.drawString(width - 170, y, f"[{data['invoice_date']}]")
    y -= 18
    c.line(60, y, width - 60, y)
    y -= 26

    # Received from
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, y, "Received from:")
    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(60, y, "Name:")
    c.drawString(140, y, f"[{data['recv_name']}]")
    y -= 14
    c.drawString(60, y, "Email:")
    c.drawString(140, y, f"[{data['recv_email']}]")
    y -= 14
    c.drawString(60, y, "Phone:")
    c.drawString(140, y, f"[{data['recv_phone']}]")
    y -= 18
    c.line(60, y, width - 60, y)
    y -= 26

    # Tour Package Details
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, y, "Tour Package Details:")
    y -= 18
    c.setFont("Helvetica", 10)

    c.drawString(60, y, "Package Name:")
    y -= 14

    pkg_lines = (data["package_name"] or "").splitlines()
    if not pkg_lines:
        pkg_lines = [""]

    for line in pkg_lines[:4]:
        c.drawString(80, y, f"[{line}]")
        y -= 14

    c.drawString(60, y, "Participation Date:")
    c.drawString(170, y, f"[{data['participation_date']}]")
    y -= 14
    c.drawString(60, y, "Number of Guests:")
    c.drawString(170, y, f"[{data['guests']}]")
    y -= 18
    c.line(60, y, width - 60, y)
    y -= 26

    # Payment Details
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, y, "Payment Details:")
    y -= 18
    c.setFont("Helvetica", 10)

    c.drawString(60, y, "Payment Method:")
    c.drawString(170, y, f"[{data['payment_method']}]")
    y -= 14

    c.drawString(60, y, "Total Amount:")
    c.drawString(170, y, f"[{int(data['total_amount']):,} KRW]")
    y -= 14

    c.drawString(60, y, "Payment Due Date:")
    c.drawString(170, y, f"[{data['pay_due_date']}]")
    y -= 14

    if data["deposit_note"]:
        c.drawString(60, y, "Note:")
        c.drawString(170, y, f"[{data['deposit_note']}]")

    c.showPage()
    c.save()
    return buf.getvalue()


# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="Tour Quotation Calculator", layout="centered")

st.title("Tour Quotation Calculator")
st.caption("견적 계산 + 손님용 Invoice PDF 출력")

# Session state: entrance spots
if "entrance_spots" not in st.session_state:
    st.session_state.entrance_spots = [
        {"place": "관광지 1", "adult_price": 0, "child_price": 0},
        {"place": "관광지 2", "adult_price": 0, "child_price": 0},
        {"place": "관광지 3", "adult_price": 0, "child_price": 0},
    ]

# Sidebar inputs
st.sidebar.header("Input")

adults = st.sidebar.number_input("Adults", min_value=0, value=2, step=1)
children = st.sidebar.number_input("Children", min_value=0, value=0, step=1)

st.sidebar.divider()

vehicle_type = st.sidebar.selectbox("Vehicle Type", ["Van", "Bus", "Other"])
vehicle_cost = st.sidebar.number_input("Vehicle Cost (KRW)", min_value=0, value=150000, step=1000)

guide_fee = st.sidebar.number_input("Guide Fee (KRW)", min_value=0, value=150000, step=1000)

st.sidebar.divider()
st.sidebar.subheader("Entrance Fees (per person)")

colA, colB = st.sidebar.columns(2)
with colA:
    if st.button("➕ 관광지 추가"):
        st.session_state.entrance_spots.append(
            {"place": f"관광지 {len(st.session_state.entrance_spots)+1}", "adult_price": 0, "child_price": 0}
        )
with colB:
    if st.button("🗑️ 관광지 하나 삭제") and len(st.session_state.entrance_spots) > 1:
        st.session_state.entrance_spots.pop()

entrance_total = 0
entrance_rows = []

for i, spot in enumerate(st.session_state.entrance_spots):
    place = st.sidebar.text_input(f"관광지 {i+1} 이름", value=spot["place"], key=f"place_{i}")

    c1, c2 = st.sidebar.columns(2)
    with c1:
        adult_price = st.number_input("성인 1인", min_value=0, value=int(spot["adult_price"]), step=1000, key=f"adult_{i}")
    with c2:
        child_price = st.number_input("아동 1인", min_value=0, value=int(spot["child_price"]), step=1000, key=f"child_{i}")

    st.session_state.entrance_spots[i]["place"] = place
    st.session_state.entrance_spots[i]["adult_price"] = adult_price
    st.session_state.entrance_spots[i]["child_price"] = child_price

    spot_total = adult_price * adults + child_price * children
    entrance_total += spot_total

    entrance_rows.append({"Item": f"Entrance - {place}", "Cost (KRW)": int(spot_total)})

st.sidebar.divider()
meal = st.sidebar.number_input("Meal Cost (total) (KRW)", min_value=0, value=0, step=1000)
other = st.sidebar.number_input("Other Cost (KRW)", min_value=0, value=0, step=1000)

margin_pct = st.sidebar.number_input("Margin %", min_value=0.0, max_value=300.0, value=20.0, step=0.5)

vat_rate = 0.10

# Calculations
total_cost = vehicle_cost + guide_fee + entrance_total + meal + other
sell_before_vat = total_cost * (1 + margin_pct / 100.0)
vat_amount = sell_before_vat * vat_rate
sell_after_vat = sell_before_vat + vat_amount

# App breakdown (screen only)
rows = [
    {"Item": f"Vehicle ({vehicle_type})", "Cost (KRW)": int(vehicle_cost)},
    {"Item": "Guide", "Cost (KRW)": int(guide_fee)},
]
rows += entrance_rows
rows += [
    {"Item": "Meal", "Cost (KRW)": int(meal)},
    {"Item": "Other", "Cost (KRW)": int(other)},
]
df = pd.DataFrame(rows)

st.subheader("Breakdown (내부 확인용)")
st.dataframe(df, use_container_width=True, hide_index=True)

m1, m2, m3 = st.columns(3)
m1.metric("Total Cost", krw(total_cost))
m2.metric("Total Sell (Before VAT)", krw(sell_before_vat))
m3.metric("Total Sell (After VAT 10%)", krw(sell_after_vat))
st.caption(f"VAT 10% = {krw(vat_amount)}")

st.divider()

# Invoice fields (PDF)
st.subheader("Invoice (손님용 PDF)")

with st.expander("Invoice fields (PDF에 출력될 항목만)", expanded=True):
    ic1, ic2 = st.columns(2)
    with ic1:
        invoice_no = st.text_input("Invoice No", value="26020401")
    with ic2:
        invoice_date = st.text_input("Date", value="26/02/04")

    st.markdown("**Received from**")
    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        recv_name = st.text_input("Name", value="")
    with rc2:
        recv_email = st.text_input("Email", value="")
    with rc3:
        recv_phone = st.text_input("Phone", value="")

    st.markdown("**Tour Package Details**")
    package_name = st.text_area("Package Name", value="", height=80)
    tc1, tc2 = st.columns(2)
    with tc1:
        participation_date = st.text_input("Participation Date", value="")
    with tc2:
        guests = st.text_input("Number of Guests", value=f"{adults + children} Pax")

    st.markdown("**Payment Details**")
    pc1, pc2 = st.columns(2)
    with pc1:
        payment_method = st.text_input("Payment Method", value="Credit Card")
    with pc2:
        total_amount = st.number_input("Total Amount (KRW)", min_value=0, value=int(sell_after_vat), step=1000)

    pay_due_date = st.text_input("Payment Due Date", value="")
    deposit_note = st.text_input("Note", value="50% at least")

invoice_data = {
    "invoice_no": invoice_no.strip(),
    "invoice_date": invoice_date.strip(),
    "recv_name": recv_name.strip(),
    "recv_email": recv_email.strip(),
    "recv_phone": recv_phone.strip(),
    "package_name": package_name.strip(),
    "participation_date": participation_date.strip(),
    "guests": guests.strip(),
    "payment_method": payment_method.strip(),
    "total_amount": total_amount,
    "pay_due_date": pay_due_date.strip(),
    "deposit_note": deposit_note.strip(),
}

pdf_bytes = build_invoice_pdf(invoice_data)

safe_name = (recv_name or "customer").strip().replace(" ", "_")

st.download_button(
    "⬇️ Download Invoice PDF",
    data=pdf_bytes,
    file_name=f"invoice_{safe_name}_{invoice_no}.pdf",
    mime="application/pdf",
)

