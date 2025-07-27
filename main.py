import streamlit as st
import requests
import time

# ---------------------
# CONSTANTS & STATE
# ---------------------
reason_labels = {
    "Spam": "1",
    "Self Injury": "2",
    "Drugs": "3",
    "Nudity": "4",
    "Violence": "5",
    "Hate Speech": "6",
    "Harassment": "7",
    "Impersonation (Insta)": "8",
    "Impersonation (Business)": "9",
    "Impersonation (Other)": "10",
    "Underage (<13)": "11",
    "Gun Sales": "12",
    "Violence (Type 1)": "13",
    "Violence (Type 4)": "14"
}

# ---------------------
# HELPER FUNCTIONS
# ---------------------
def get_user_id(username, sessionid):
    try:
        r = requests.get(
            f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}",
            headers={
                "User-Agent": "Instagram 155.0.0.37.107",
                "Cookie": f"sessionid={sessionid};",
            }
        )
        return r.json()["data"]["user"]["id"]
    except:
        return None

def send_report(user_id, sessionid, csrftoken, reason):
    res = requests.post(
        f"https://i.instagram.com/users/{user_id}/flag/",
        headers={
            "User-Agent": "Mozilla/5.0",
            "Host": "i.instagram.com",
            "cookie": f"sessionid={sessionid}",
            "X-CSRFToken": csrftoken,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        },
        data=f'source_name=&reason_id={reason}&frx_context=',
        allow_redirects=False
    )
    return res.status_code

# ---------------------
# STREAMLIT UI
# ---------------------
st.set_page_config(page_title="Instagram Reporter", layout="centered")
st.title("📢 Instagram Multi-Report Tool (7 Logins Supported)")

accounts = []
st.subheader("👥 Instagram Accounts (up to 7)")
for i in range(7):
    with st.expander(f"🔐 Account {i+1}"):
        sid = st.text_input(f"Session ID {i+1}", type="password", key=f"sid_{i}")
        csrf = st.text_input(f"CSRF Token {i+1}", type="password", key=f"csrf_{i}")
        if sid and csrf:
            accounts.append({"sessionid": sid, "csrftoken": csrf})

with st.form("report_form"):
    targets = st.text_area("🎯 Target Usernames (comma-separated)")
    report_reason = st.selectbox("🚨 Report Reason", list(reason_labels.keys()))
    report_count = st.number_input("🔁 Reports per target", min_value=1, max_value=100, value=5)
    delay = st.slider("⏱️ Delay between reports (seconds)", min_value=1, max_value=30, value=5)
    submit = st.form_submit_button("🚀 Start Reporting")

if submit:
    if not accounts:
        st.error("⚠️ Please fill in at least one session ID and CSRF token.")
    elif not targets:
        st.error("⚠️ Please enter at least one target username.")
    else:
        usernames = [u.strip() for u in targets.split(",") if u.strip()]
        reason_code = reason_labels[report_reason]

        st.info(f"Starting reports for {len(usernames)} user(s) using {len(accounts)} account(s)...")
        report_log = st.empty()
        log_lines = []

        for username in usernames:
            user_id = None
            for acc in accounts:
                user_id = get_user_id(username, acc["sessionid"])
                if user_id:
                    break
            if not user_id:
                log_lines.append(f"❌ @{username} not found using any account.")
                report_log.text("\n".join(log_lines))
                continue

            for i in range(report_count):
                acc = accounts[i % len(accounts)]  # Rotate accounts
                code = send_report(user_id, acc["sessionid"], acc["csrftoken"], reason_code)
                if code in [200, 302]:
                    log_lines.append(f"✅ @{username} report {i+1}/{report_count} (Acc {i % len(accounts)+1})")
                elif code == 429:
                    log_lines.append(f"🚫 @{username} rate limited (Acc {i % len(accounts)+1})")
                    continue
                else:
                    log_lines.append(f"⚠️ @{username} unknown response: {code}")
                report_log.text("\n".join(log_lines))
                time.sleep(delay)

        st.success("🎉 Reporting complete!")
