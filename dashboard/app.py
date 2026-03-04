"""Synup SDK Explorer — interactive dashboard to browse and test all SDK endpoints.

Run:
    pip install -r requirements.txt
    SYNUP_API_KEY=your_key streamlit run app.py
"""

import inspect
import json
import os
import traceback
from typing import Any, get_type_hints

import streamlit as st
from synup import SynupClient, SynupAPIError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_public_methods(client: SynupClient) -> list[tuple[str, Any]]:
    """Return (name, method) pairs for all public SDK methods."""
    methods = []
    for name in sorted(dir(client)):
        if name.startswith("_"):
            continue
        attr = getattr(client, name)
        if callable(attr):
            methods.append((name, attr))
    return methods


def parse_param_type(annotation: Any) -> str:
    """Return a human-readable type string."""
    if annotation is inspect.Parameter.empty:
        return "any"
    origin = getattr(annotation, "__origin__", None)
    if origin is not None:
        args = getattr(annotation, "__args__", ())
        args_str = ", ".join(parse_param_type(a) for a in args if a is not type(None))
        return f"{getattr(origin, '__name__', str(origin))}[{args_str}]"
    if hasattr(annotation, "__name__"):
        return annotation.__name__
    return str(annotation)


def get_method_info(method: Any) -> dict:
    """Extract signature, docstring, and parameter details for a method."""
    sig = inspect.signature(method)
    doc = inspect.getdoc(method) or ""
    params = []
    for pname, param in sig.parameters.items():
        if pname == "self":
            continue
        params.append({
            "name": pname,
            "type": parse_param_type(param.annotation),
            "default": None if param.default is inspect.Parameter.empty else param.default,
            "required": param.default is inspect.Parameter.empty,
        })
    return {"doc": doc, "params": params}


CATEGORY_PREFIXES = {
    "Locations": ["fetch_all_locations", "fetch_locations_by", "search_locations",
                   "create_location", "update_location", "archive_locations",
                   "activate_locations", "cancel_archive_locations",
                   "fetch_locations_by_folder", "fetch_locations_by_tags"],
    "Listings": ["fetch_premium_listings", "fetch_voice_listings", "fetch_additional_listings",
                 "fetch_duplicate_listings", "fetch_all_duplicate_listings", "fetch_ai_listings",
                 "mark_listings_as_duplicate", "mark_listings_as_not_duplicate"],
    "Reviews": ["fetch_interactions", "fetch_review_settings", "respond_to_review",
                "edit_review_response", "archive_review_response", "edit_review_settings",
                "fetch_review_analytics", "fetch_review_details", "fetch_review_phrases",
                "fetch_review_site_config"],
    "Review Campaigns": ["fetch_review_campaigns", "create_review_campaign",
                         "add_review_campaign_customers", "fetch_review_campaign_customers"],
    "Analytics": ["fetch_google_analytics", "fetch_bing_analytics", "fetch_facebook_analytics"],
    "Rankings": ["fetch_keywords", "fetch_keywords_performance", "add_keywords",
                 "archive_keyword", "fetch_ranking_analytics", "fetch_ranking_sitewise"],
    "Grid Rank": ["create_grid_report", "fetch_grid_report", "fetch_location_grid_reports"],
    "Photos": ["fetch_location_photos", "add_location_photos", "remove_location_photos",
               "star_location_photos", "fetch_photo_upload_status"],
    "Folders": ["create_folder", "rename_folder", "delete_folder",
                "add_locations_to_folder", "remove_locations_from_folder",
                "fetch_folders_flat", "fetch_folders_tree", "fetch_folder_details"],
    "Tags": ["add_location_tag", "remove_location_tag", "fetch_tags"],
    "Users": ["fetch_users", "create_user", "update_user", "add_user_locations",
              "remove_user_locations", "add_user_folders", "remove_user_folders",
              "add_user_and_folder", "fetch_user_resources", "fetch_users_by_ids", "fetch_roles"],
    "Connected Accounts": ["connect_google_account", "connect_facebook_account",
                           "disconnect_google_account", "disconnect_facebook_account",
                           "trigger_connected_account_matches", "fetch_connected_account",
                           "confirm_connected_account_matches", "connect_listing",
                           "disconnect_listing", "create_gmb_listing", "fetch_connection"],
    "OAuth": ["get_oauth_connect_url", "oauth_disconnect"],
    "Automations": ["create_temporary_close_automation"],
    "Account": ["fetch_plan_sites", "fetch_countries", "fetch_subscriptions"],
}


def categorize_method(name: str) -> str:
    for category, prefixes in CATEGORY_PREFIXES.items():
        for prefix in prefixes:
            if name.startswith(prefix):
                return category
    return "Other"


def render_input(param: dict, key_prefix: str) -> Any:
    """Render a Streamlit input widget for a parameter and return its value."""
    pname = param["name"]
    ptype = param["type"]
    default = param["default"]
    key = f"{key_prefix}_{pname}"

    label = f"**{pname}**" + (" *(required)*" if param["required"] else "")

    if ptype in ("int", "float"):
        default_val = default if default is not None else 0
        if ptype == "int":
            return st.number_input(label, value=int(default_val), step=1, key=key)
        return st.number_input(label, value=float(default_val), key=key)

    if ptype == "bool":
        default_val = default if default is not None else False
        return st.checkbox(label, value=default_val, key=key)

    if "list" in ptype.lower() or "dict" in ptype.lower():
        help_text = f"Enter as JSON ({ptype})"
        default_str = json.dumps(default) if default is not None else ""
        raw = st.text_area(label, value=default_str, help=help_text, key=key)
        if raw.strip():
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                st.warning(f"Invalid JSON for {pname}")
                return None
        return default

    # Default: string input
    default_str = str(default) if default is not None else ""
    val = st.text_input(label, value=default_str, key=key)
    if not val and not param["required"]:
        return default
    # Try to coerce to int if the type hint suggests it
    if "int" in ptype and val.isdigit():
        return int(val)
    return val if val else default


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Synup SDK Explorer", page_icon="🔍", layout="wide")
st.title("Synup SDK Explorer")
st.caption("Browse, test, and explore all Synup SDK endpoints interactively.")

# Sidebar: API key
api_key = st.sidebar.text_input("API Key", value=os.environ.get("SYNUP_API_KEY", ""), type="password")

if not api_key:
    st.info("Enter your Synup API key in the sidebar to get started.")
    st.stop()

client = SynupClient(api_key=api_key)
methods = get_public_methods(client)

# Sidebar: category filter
categories = sorted(set(categorize_method(name) for name, _ in methods))
selected_category = st.sidebar.selectbox("Category", ["All"] + categories)

# Sidebar: search
search = st.sidebar.text_input("Search methods", "")

# Filter methods
filtered = []
for name, method in methods:
    cat = categorize_method(name)
    if selected_category != "All" and cat != selected_category:
        continue
    if search and search.lower() not in name.lower():
        continue
    filtered.append((name, method, cat))

# Main content
if not filtered:
    st.warning("No methods match your filter.")
    st.stop()

# Method selector
method_names = [name for name, _, _ in filtered]
selected_name = st.selectbox(
    "Select endpoint",
    method_names,
    format_func=lambda x: f"{categorize_method(x)} / {x}",
)

selected_method = None
for name, method, cat in filtered:
    if name == selected_name:
        selected_method = method
        break

if selected_method is None:
    st.stop()

info = get_method_info(selected_method)

# Display method info
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader(selected_name)
    # Show docstring
    doc_lines = info["doc"].split("\n")
    summary = doc_lines[0] if doc_lines else ""
    st.markdown(summary)

    # Show full docstring in expander
    if len(doc_lines) > 1:
        with st.expander("Full documentation"):
            st.text(info["doc"])

with col2:
    st.markdown(f"**Category:** {categorize_method(selected_name)}")
    st.markdown(f"**Parameters:** {len(info['params'])}")
    required_count = sum(1 for p in info["params"] if p["required"])
    st.markdown(f"**Required:** {required_count}")

# Parameter form
st.markdown("---")
st.subheader("Parameters")

if not info["params"]:
    st.info("This method takes no parameters.")

param_values = {}
cols = st.columns(2)
for i, param in enumerate(info["params"]):
    with cols[i % 2]:
        val = render_input(param, selected_name)
        param_values[param["name"]] = val

# Execute
st.markdown("---")
if st.button("Execute", type="primary", use_container_width=True):
    # Build kwargs, skip None optional params
    kwargs = {}
    for param in info["params"]:
        val = param_values.get(param["name"])
        if val is None and not param["required"]:
            continue
        if val == "" and not param["required"]:
            continue
        kwargs[param["name"]] = val

    with st.spinner(f"Calling {selected_name}..."):
        try:
            result = selected_method(**kwargs)
            st.success("Success")

            # Show result
            if isinstance(result, (dict, list)):
                st.json(result)
            else:
                st.write(result)

        except SynupAPIError as e:
            st.error(f"API Error: {e} (status {e.status_code})")
            if e.response_body:
                with st.expander("Response body"):
                    st.code(e.response_body)
        except Exception as e:
            st.error(f"Error: {e}")
            with st.expander("Traceback"):
                st.code(traceback.format_exc())
