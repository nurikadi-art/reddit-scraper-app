#!/usr/bin/env python3
"""
Notion Power Dashboard Creator
Creates a comprehensive project management dashboard in Notion with:
- 4 Project workspaces (Personal, Dr. Berg, Recrutu, Smartworker)
- Daily Planner with time blocks
- Statistics & KPI Tracker
- Sample data to get started immediately
"""

import os
import sys
from datetime import date
from notion_client import Client


# ─────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────

def create_power_dashboard(notion_token):
    """
    Create the complete Power Dashboard in Notion.

    Args:
        notion_token: Notion Internal Integration Token (ntn_...)

    Returns:
        dict with dashboard page ID, URL, and all database IDs
    """
    notion = Client(auth=notion_token)
    print("\n" + "=" * 60)
    print("  POWER DASHBOARD CREATOR")
    print("=" * 60)

    # ── Step 1: Create the main dashboard page ──────────────────────
    print("\n[1/8] Creating dashboard page...")
    dashboard_page = notion.pages.create(
        parent={"workspace": True},
        icon={"type": "emoji", "emoji": "🎯"},
        cover={
            "type": "external",
            "external": {
                "url": "https://images.unsplash.com/photo-1484480974693-6ca0a78fb36b?w=1500"
            }
        },
        properties={
            "title": {
                "title": [
                    {"text": {"content": "Power Dashboard"}}
                ]
            }
        }
    )
    page_id = dashboard_page["id"]
    page_url = dashboard_page.get("url", f"https://notion.so/{page_id.replace('-', '')}")
    print(f"    Page created: {page_url}")

    # ── Step 2: Add hero header with workspace cards ────────────────
    print("[2/8] Building header section...")
    _add_header_blocks(notion, page_id)

    # ── Step 3: Daily Planner ───────────────────────────────────────
    print("[3/8] Creating Daily Planner...")
    _add_section_header(
        notion, page_id,
        "📋 Today's Plan",
        "Plan your day with time blocks, priorities, and energy levels. One task at a time."
    )
    daily_db = _create_daily_planner_db(notion, page_id)

    # ── Step 4: Statistics & KPIs ───────────────────────────────────
    print("[4/8] Creating Statistics Tracker...")
    _add_section_header(
        notion, page_id,
        "📊 Statistics & KPIs",
        "Track metrics across all businesses. Update weekly for trend insights."
    )
    stats_db = _create_statistics_db(notion, page_id)

    # ── Step 5-8: Project Databases ─────────────────────────────────
    workspaces = [
        ("👤 Personal Projects", "Personal goals, learning, health, and side projects.", "personal"),
        ("🏥 Dr. Berg Projects", "Content production, campaigns, audience growth, and brand initiatives.", "dr_berg"),
        ("💼 Recrutu Business Projects", "Platform features, client acquisition, operations, and growth.", "recrutu"),
        ("🧠 Smartworker Projects", "Product development, AI tools, automations, and strategy.", "smartworker"),
    ]

    project_dbs = {}
    for i, (title, desc, key) in enumerate(workspaces, 5):
        print(f"[{i}/8] Creating {title}...")
        _add_section_header(notion, page_id, title, desc)
        db = _create_project_db(notion, page_id, title)
        project_dbs[key] = db

    # ── Populate with starter data ──────────────────────────────────
    print("\n    Adding starter data...")
    _add_sample_daily_tasks(notion, daily_db["id"])
    _add_sample_statistics(notion, stats_db["id"])
    _add_sample_projects(notion, project_dbs)

    # ── Done ────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  POWER DASHBOARD READY!")
    print(f"  {page_url}")
    print("=" * 60 + "\n")

    return {
        "dashboard_page_id": page_id,
        "dashboard_url": page_url,
        "daily_planner_db_id": daily_db["id"],
        "statistics_db_id": stats_db["id"],
        "project_dbs": {k: v["id"] for k, v in project_dbs.items()},
    }


# ─────────────────────────────────────────────────────────────────────
# PAGE LAYOUT BLOCKS
# ─────────────────────────────────────────────────────────────────────

def _add_header_blocks(notion, page_id):
    """Add the hero section: main callout + 4 workspace summary cards."""
    notion.blocks.children.append(
        block_id=page_id,
        children=[
            # ── Hero callout ────────────────────────────────────────
            {
                "type": "callout",
                "callout": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "POWER DASHBOARD"},
                            "annotations": {"bold": True}
                        },
                        {
                            "type": "text",
                            "text": {"content": " — Command Center\nTrack every project, plan your day, and monitor KPIs across all your businesses from one place."}
                        }
                    ],
                    "icon": {"type": "emoji", "emoji": "🎯"},
                    "color": "blue_background"
                }
            },
            # ── 4 workspace summary cards in columns ────────────────
            {
                "type": "column_list",
                "column_list": {
                    "children": [
                        _col_card("👤", "Personal", "purple_background"),
                        _col_card("🏥", "Dr. Berg", "green_background"),
                        _col_card("💼", "Recrutu", "yellow_background"),
                        _col_card("🧠", "Smartworker", "orange_background"),
                    ]
                }
            },
            # ── Quick-nav heading ───────────────────────────────────
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Scroll down for: "},
                            "annotations": {"color": "gray"}
                        },
                        {
                            "type": "text",
                            "text": {"content": "Daily Plan"},
                            "annotations": {"bold": True, "color": "blue"}
                        },
                        {
                            "type": "text",
                            "text": {"content": " · "},
                            "annotations": {"color": "gray"}
                        },
                        {
                            "type": "text",
                            "text": {"content": "Statistics"},
                            "annotations": {"bold": True, "color": "purple"}
                        },
                        {
                            "type": "text",
                            "text": {"content": " · "},
                            "annotations": {"color": "gray"}
                        },
                        {
                            "type": "text",
                            "text": {"content": "All Project Boards"},
                            "annotations": {"bold": True, "color": "orange"}
                        }
                    ]
                }
            },
            {"type": "divider", "divider": {}},
        ]
    )


def _col_card(emoji, label, color):
    """Build a single column card for the workspace header."""
    return {
        "type": "column",
        "column": {
            "children": [
                {
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": label},
                                "annotations": {"bold": True}
                            }
                        ],
                        "icon": {"type": "emoji", "emoji": emoji},
                        "color": color
                    }
                }
            ]
        }
    }


def _add_section_header(notion, page_id, title, description):
    """Add a visual section divider with heading + description."""
    notion.blocks.children.append(
        block_id=page_id,
        children=[
            {"type": "divider", "divider": {}},
            {
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": title}}]
                }
            },
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": description},
                            "annotations": {"italic": True, "color": "gray"}
                        }
                    ]
                }
            }
        ]
    )


# ─────────────────────────────────────────────────────────────────────
# DATABASE SCHEMAS
# ─────────────────────────────────────────────────────────────────────

def _create_daily_planner_db(notion, page_id):
    """Create the Daily Planner database with time blocks + energy tracking."""
    return notion.databases.create(
        parent={"type": "page_id", "page_id": page_id},
        is_inline=True,
        icon={"type": "emoji", "emoji": "📋"},
        title=[{"type": "text", "text": {"content": "Daily Plan"}}],
        properties={
            "Task": {"title": {}},
            "Done": {"checkbox": {}},
            "Priority": {
                "select": {
                    "options": [
                        {"name": "🔴 Must Do", "color": "red"},
                        {"name": "🟡 Should Do", "color": "yellow"},
                        {"name": "🟢 Nice to Have", "color": "green"},
                    ]
                }
            },
            "Time Block": {
                "select": {
                    "options": [
                        {"name": "🌅 Early Morning (6-8)", "color": "yellow"},
                        {"name": "☀️ Morning (8-10)", "color": "orange"},
                        {"name": "🌤️ Late Morning (10-12)", "color": "red"},
                        {"name": "🌞 Afternoon (12-3)", "color": "pink"},
                        {"name": "🌇 Late Afternoon (3-5)", "color": "purple"},
                        {"name": "🌆 Evening (5-7)", "color": "blue"},
                        {"name": "🌙 Night (7+)", "color": "gray"},
                    ]
                }
            },
            "Category": {
                "select": {
                    "options": [
                        {"name": "👤 Personal", "color": "purple"},
                        {"name": "🏥 Dr. Berg", "color": "green"},
                        {"name": "💼 Recrutu", "color": "yellow"},
                        {"name": "🧠 Smartworker", "color": "orange"},
                        {"name": "💪 Health", "color": "red"},
                        {"name": "📚 Learning", "color": "blue"},
                    ]
                }
            },
            "Duration": {
                "select": {
                    "options": [
                        {"name": "15 min", "color": "gray"},
                        {"name": "30 min", "color": "blue"},
                        {"name": "1 hour", "color": "green"},
                        {"name": "2 hours", "color": "yellow"},
                        {"name": "3+ hours", "color": "red"},
                    ]
                }
            },
            "Energy": {
                "select": {
                    "options": [
                        {"name": "⚡ High Focus", "color": "red"},
                        {"name": "💡 Medium Focus", "color": "yellow"},
                        {"name": "🧘 Low Focus", "color": "green"},
                    ]
                }
            },
            "Date": {"date": {}},
            "Notes": {"rich_text": {}},
        }
    )


def _create_statistics_db(notion, page_id):
    """Create the Statistics & KPI Tracker database."""
    return notion.databases.create(
        parent={"type": "page_id", "page_id": page_id},
        is_inline=True,
        icon={"type": "emoji", "emoji": "📊"},
        title=[{"type": "text", "text": {"content": "Statistics & KPIs"}}],
        properties={
            "Metric": {"title": {}},
            "Category": {
                "select": {
                    "options": [
                        {"name": "💰 Revenue", "color": "green"},
                        {"name": "📈 Growth", "color": "blue"},
                        {"name": "📱 Content", "color": "purple"},
                        {"name": "💪 Health", "color": "red"},
                        {"name": "⚡ Productivity", "color": "yellow"},
                        {"name": "🎯 Custom", "color": "gray"},
                    ]
                }
            },
            "Value": {"number": {"format": "number"}},
            "Target": {"number": {"format": "number"}},
            "Unit": {"rich_text": {}},
            "Date": {"date": {}},
            "Trend": {
                "select": {
                    "options": [
                        {"name": "📈 Up", "color": "green"},
                        {"name": "📉 Down", "color": "red"},
                        {"name": "➡️ Stable", "color": "yellow"},
                        {"name": "🆕 New", "color": "blue"},
                    ]
                }
            },
            "Workspace": {
                "select": {
                    "options": [
                        {"name": "👤 Personal", "color": "purple"},
                        {"name": "🏥 Dr. Berg", "color": "green"},
                        {"name": "💼 Recrutu", "color": "yellow"},
                        {"name": "🧠 Smartworker", "color": "orange"},
                        {"name": "🌐 Overall", "color": "blue"},
                    ]
                }
            },
            "Notes": {"rich_text": {}},
        }
    )


def _create_project_db(notion, page_id, title):
    """Create a Project board database (used for each workspace)."""
    return notion.databases.create(
        parent={"type": "page_id", "page_id": page_id},
        is_inline=True,
        icon={"type": "emoji", "emoji": title[0]},
        title=[{"type": "text", "text": {"content": title}}],
        properties={
            "Project": {"title": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "💭 Backlog", "color": "default"},
                        {"name": "📋 To Do", "color": "blue"},
                        {"name": "🔨 In Progress", "color": "yellow"},
                        {"name": "👀 In Review", "color": "orange"},
                        {"name": "✅ Done", "color": "green"},
                        {"name": "📦 Archived", "color": "brown"},
                    ]
                }
            },
            "Priority": {
                "select": {
                    "options": [
                        {"name": "🚨 Urgent", "color": "red"},
                        {"name": "🔴 High", "color": "orange"},
                        {"name": "🟡 Medium", "color": "yellow"},
                        {"name": "🟢 Low", "color": "green"},
                    ]
                }
            },
            "Type": {
                "select": {
                    "options": [
                        {"name": "🚀 Feature", "color": "blue"},
                        {"name": "🐛 Bug Fix", "color": "red"},
                        {"name": "📝 Content", "color": "purple"},
                        {"name": "🔍 Research", "color": "yellow"},
                        {"name": "📣 Marketing", "color": "pink"},
                        {"name": "🎨 Design", "color": "orange"},
                        {"name": "💻 Development", "color": "green"},
                        {"name": "📊 Analytics", "color": "gray"},
                    ]
                }
            },
            "Due Date": {"date": {}},
            "Progress": {"number": {"format": "percent"}},
            "Owner": {"rich_text": {}},
            "Tags": {
                "multi_select": {
                    "options": [
                        {"name": "MVP", "color": "red"},
                        {"name": "Quick Win", "color": "green"},
                        {"name": "Long Term", "color": "blue"},
                        {"name": "Revenue", "color": "yellow"},
                        {"name": "Automation", "color": "purple"},
                        {"name": "Content", "color": "pink"},
                        {"name": "Infrastructure", "color": "gray"},
                        {"name": "Client Facing", "color": "orange"},
                    ]
                }
            },
            "Budget": {"number": {"format": "dollar"}},
            "Impact": {
                "select": {
                    "options": [
                        {"name": "🔥 High Impact", "color": "red"},
                        {"name": "💡 Medium Impact", "color": "yellow"},
                        {"name": "📌 Low Impact", "color": "green"},
                    ]
                }
            },
            "URL": {"url": {}},
            "Notes": {"rich_text": {}},
        }
    )


# ─────────────────────────────────────────────────────────────────────
# SAMPLE / STARTER DATA
# ─────────────────────────────────────────────────────────────────────

def _add_sample_daily_tasks(notion, db_id):
    """Seed the Daily Planner with realistic example tasks."""
    today = date.today().isoformat()

    tasks = [
        {
            "Task": "Gym + cold shower",
            "Priority": "🔴 Must Do",
            "Time Block": "🌅 Early Morning (6-8)",
            "Category": "💪 Health",
            "Duration": "1 hour",
            "Energy": "⚡ High Focus",
        },
        {
            "Task": "Review Recrutu analytics & user feedback",
            "Priority": "🔴 Must Do",
            "Time Block": "☀️ Morning (8-10)",
            "Category": "💼 Recrutu",
            "Duration": "30 min",
            "Energy": "⚡ High Focus",
        },
        {
            "Task": "Record Dr. Berg video script",
            "Priority": "🔴 Must Do",
            "Time Block": "🌤️ Late Morning (10-12)",
            "Category": "🏥 Dr. Berg",
            "Duration": "2 hours",
            "Energy": "⚡ High Focus",
        },
        {
            "Task": "Smartworker feature planning session",
            "Priority": "🟡 Should Do",
            "Time Block": "🌞 Afternoon (12-3)",
            "Category": "🧠 Smartworker",
            "Duration": "1 hour",
            "Energy": "💡 Medium Focus",
        },
        {
            "Task": "Team sync + Slack catch-up",
            "Priority": "🟡 Should Do",
            "Time Block": "🌇 Late Afternoon (3-5)",
            "Category": "💼 Recrutu",
            "Duration": "30 min",
            "Energy": "💡 Medium Focus",
        },
        {
            "Task": "Content ideas brainstorm",
            "Priority": "🟢 Nice to Have",
            "Time Block": "🌆 Evening (5-7)",
            "Category": "👤 Personal",
            "Duration": "30 min",
            "Energy": "🧘 Low Focus",
        },
        {
            "Task": "Read 30 pages + journal",
            "Priority": "🟢 Nice to Have",
            "Time Block": "🌙 Night (7+)",
            "Category": "📚 Learning",
            "Duration": "30 min",
            "Energy": "🧘 Low Focus",
        },
    ]

    for task in tasks:
        notion.pages.create(
            parent={"database_id": db_id},
            properties={
                "Task": _title(task["Task"]),
                "Done": {"checkbox": False},
                "Priority": _select(task["Priority"]),
                "Time Block": _select(task["Time Block"]),
                "Category": _select(task["Category"]),
                "Duration": _select(task["Duration"]),
                "Energy": _select(task["Energy"]),
                "Date": {"date": {"start": today}},
            }
        )


def _add_sample_statistics(notion, db_id):
    """Seed the Statistics Tracker with KPI templates."""
    today = date.today().isoformat()

    stats = [
        # Revenue
        {"Metric": "Total Monthly Revenue", "Category": "💰 Revenue", "Value": 0, "Target": 50000, "Unit": "USD", "Trend": "🆕 New", "Workspace": "🌐 Overall"},
        {"Metric": "Recrutu MRR", "Category": "💰 Revenue", "Value": 0, "Target": 20000, "Unit": "USD", "Trend": "🆕 New", "Workspace": "💼 Recrutu"},
        {"Metric": "Dr. Berg Revenue", "Category": "💰 Revenue", "Value": 0, "Target": 15000, "Unit": "USD", "Trend": "🆕 New", "Workspace": "🏥 Dr. Berg"},
        {"Metric": "Smartworker Revenue", "Category": "💰 Revenue", "Value": 0, "Target": 10000, "Unit": "USD", "Trend": "🆕 New", "Workspace": "🧠 Smartworker"},
        # Growth
        {"Metric": "YouTube Subscribers", "Category": "📈 Growth", "Value": 0, "Target": 100000, "Unit": "subs", "Trend": "🆕 New", "Workspace": "🏥 Dr. Berg"},
        {"Metric": "Recrutu Active Users", "Category": "📈 Growth", "Value": 0, "Target": 1000, "Unit": "users", "Trend": "🆕 New", "Workspace": "💼 Recrutu"},
        {"Metric": "Smartworker Beta Users", "Category": "📈 Growth", "Value": 0, "Target": 500, "Unit": "users", "Trend": "🆕 New", "Workspace": "🧠 Smartworker"},
        {"Metric": "Email List Size", "Category": "📈 Growth", "Value": 0, "Target": 10000, "Unit": "emails", "Trend": "🆕 New", "Workspace": "🌐 Overall"},
        # Content
        {"Metric": "Videos Published This Month", "Category": "📱 Content", "Value": 0, "Target": 20, "Unit": "videos", "Trend": "🆕 New", "Workspace": "🏥 Dr. Berg"},
        {"Metric": "Scripts Generated", "Category": "📱 Content", "Value": 0, "Target": 100, "Unit": "scripts", "Trend": "🆕 New", "Workspace": "🧠 Smartworker"},
        # Health & Productivity
        {"Metric": "Workout Days This Week", "Category": "💪 Health", "Value": 0, "Target": 5, "Unit": "days", "Trend": "🆕 New", "Workspace": "👤 Personal"},
        {"Metric": "Daily Productivity Score", "Category": "⚡ Productivity", "Value": 0, "Target": 9, "Unit": "/10", "Trend": "🆕 New", "Workspace": "👤 Personal"},
        {"Metric": "Deep Work Hours Today", "Category": "⚡ Productivity", "Value": 0, "Target": 6, "Unit": "hours", "Trend": "🆕 New", "Workspace": "👤 Personal"},
    ]

    for s in stats:
        notion.pages.create(
            parent={"database_id": db_id},
            properties={
                "Metric": _title(s["Metric"]),
                "Category": _select(s["Category"]),
                "Value": {"number": s["Value"]},
                "Target": {"number": s["Target"]},
                "Unit": _rich_text(s["Unit"]),
                "Date": {"date": {"start": today}},
                "Trend": _select(s["Trend"]),
                "Workspace": _select(s["Workspace"]),
            }
        )


def _add_sample_projects(notion, project_dbs):
    """Seed each workspace with realistic starter projects."""
    samples = {
        "personal": [
            {"Project": "Morning Routine Optimization", "Status": "🔨 In Progress", "Priority": "🔴 High", "Type": "🔍 Research", "Progress": 0.4, "Tags": ["Quick Win"], "Impact": "🔥 High Impact"},
            {"Project": "Learn Advanced Python & AI", "Status": "🔨 In Progress", "Priority": "🟡 Medium", "Type": "📝 Content", "Progress": 0.3, "Tags": ["Long Term"], "Impact": "💡 Medium Impact"},
            {"Project": "Financial Dashboard Setup", "Status": "📋 To Do", "Priority": "🟡 Medium", "Type": "📊 Analytics", "Progress": 0, "Tags": ["Quick Win", "Automation"], "Impact": "💡 Medium Impact"},
            {"Project": "Networking Strategy 2026", "Status": "💭 Backlog", "Priority": "🟢 Low", "Type": "📣 Marketing", "Progress": 0, "Tags": ["Long Term"], "Impact": "📌 Low Impact"},
        ],
        "dr_berg": [
            {"Project": "Weekly Content Calendar Q1", "Status": "🔨 In Progress", "Priority": "🚨 Urgent", "Type": "📝 Content", "Progress": 0.5, "Tags": ["Content", "Revenue"], "Impact": "🔥 High Impact"},
            {"Project": "New Video Series: Myth Busters", "Status": "📋 To Do", "Priority": "🔴 High", "Type": "📝 Content", "Progress": 0, "Tags": ["Content", "Long Term"], "Impact": "🔥 High Impact"},
            {"Project": "YouTube SEO Audit", "Status": "📋 To Do", "Priority": "🔴 High", "Type": "📊 Analytics", "Progress": 0, "Tags": ["Quick Win"], "Impact": "💡 Medium Impact"},
            {"Project": "Sponsorship Outreach Campaign", "Status": "💭 Backlog", "Priority": "🟡 Medium", "Type": "📣 Marketing", "Progress": 0, "Tags": ["Revenue", "Client Facing"], "Impact": "🔥 High Impact"},
            {"Project": "Community Engagement Strategy", "Status": "💭 Backlog", "Priority": "🟡 Medium", "Type": "📣 Marketing", "Progress": 0, "Tags": ["Long Term"], "Impact": "💡 Medium Impact"},
        ],
        "recrutu": [
            {"Project": "AI Matching Algorithm v2", "Status": "🔨 In Progress", "Priority": "🚨 Urgent", "Type": "💻 Development", "Progress": 0.4, "Tags": ["MVP", "Revenue"], "Impact": "🔥 High Impact"},
            {"Project": "Client Onboarding Flow Redesign", "Status": "📋 To Do", "Priority": "🔴 High", "Type": "🎨 Design", "Progress": 0, "Tags": ["Client Facing", "Quick Win"], "Impact": "🔥 High Impact"},
            {"Project": "Automated Email Sequences", "Status": "📋 To Do", "Priority": "🔴 High", "Type": "📣 Marketing", "Progress": 0, "Tags": ["Automation", "Revenue"], "Impact": "🔥 High Impact"},
            {"Project": "Landing Page A/B Tests", "Status": "💭 Backlog", "Priority": "🟡 Medium", "Type": "🎨 Design", "Progress": 0, "Tags": ["Client Facing"], "Impact": "💡 Medium Impact"},
            {"Project": "Database Performance Optimization", "Status": "💭 Backlog", "Priority": "🟡 Medium", "Type": "💻 Development", "Progress": 0, "Tags": ["Infrastructure"], "Impact": "💡 Medium Impact"},
            {"Project": "Mobile App MVP", "Status": "💭 Backlog", "Priority": "🟢 Low", "Type": "🚀 Feature", "Progress": 0, "Tags": ["MVP", "Long Term"], "Impact": "🔥 High Impact"},
        ],
        "smartworker": [
            {"Project": "Viral Script Generator Enhancement", "Status": "🔨 In Progress", "Priority": "🔴 High", "Type": "🚀 Feature", "Progress": 0.6, "Tags": ["MVP", "Automation"], "Impact": "🔥 High Impact"},
            {"Project": "Notion Dashboard Integration", "Status": "🔨 In Progress", "Priority": "🚨 Urgent", "Type": "🚀 Feature", "Progress": 0.8, "Tags": ["MVP", "Automation"], "Impact": "🔥 High Impact"},
            {"Project": "Multi-Platform Export (TikTok, IG, YT)", "Status": "📋 To Do", "Priority": "🔴 High", "Type": "🚀 Feature", "Progress": 0, "Tags": ["Revenue", "Client Facing"], "Impact": "🔥 High Impact"},
            {"Project": "AI Prompt Library", "Status": "📋 To Do", "Priority": "🟡 Medium", "Type": "📝 Content", "Progress": 0, "Tags": ["Content", "Automation"], "Impact": "💡 Medium Impact"},
            {"Project": "User Analytics Dashboard", "Status": "💭 Backlog", "Priority": "🟡 Medium", "Type": "📊 Analytics", "Progress": 0, "Tags": ["Infrastructure"], "Impact": "💡 Medium Impact"},
        ],
    }

    for workspace, projects in samples.items():
        db_id = project_dbs[workspace]["id"]
        for proj in projects:
            properties = {
                "Project": _title(proj["Project"]),
                "Status": _select(proj["Status"]),
                "Priority": _select(proj["Priority"]),
                "Type": _select(proj["Type"]),
                "Progress": {"number": proj["Progress"]},
                "Tags": {"multi_select": [{"name": t} for t in proj["Tags"]]},
                "Impact": _select(proj["Impact"]),
            }
            notion.pages.create(parent={"database_id": db_id}, properties=properties)


# ─────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────

def _title(text):
    return {"title": [{"text": {"content": text}}]}

def _rich_text(text):
    return {"rich_text": [{"text": {"content": text}}]}

def _select(name):
    return {"select": {"name": name}}


# ─────────────────────────────────────────────────────────────────────
# SCRIPT EXPORT UTILITY  (for pushing viral scripts to Notion)
# ─────────────────────────────────────────────────────────────────────

def export_scripts_to_notion(notion_token, database_id, scripts):
    """
    Export generated viral scripts to a Notion database.

    Args:
        notion_token: Notion API token
        database_id: ID of the target Notion database
        scripts: List of script dicts from the generator
    """
    notion = Client(auth=notion_token)
    exported = 0

    for script in scripts:
        try:
            notion.pages.create(
                parent={"database_id": database_id},
                properties={
                    "Project": _title(script.get("post_title", script.get("title", "Untitled Script"))),
                    "Status": _select("📋 To Do"),
                    "Type": _select("📝 Content"),
                    "Priority": _select("🟡 Medium"),
                    "Tags": {"multi_select": [{"name": "Content"}, {"name": "Automation"}]},
                    "Notes": _rich_text(script.get("script", "")[:2000]),
                    "URL": {"url": script.get("post_url", script.get("url", None))},
                },
            )
            exported += 1
        except Exception as e:
            print(f"    Failed to export '{script.get('title', '?')}': {e}")

    print(f"    Exported {exported}/{len(scripts)} scripts to Notion")
    return exported


# ─────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    token = os.getenv("NOTION_API_KEY")

    if not token and len(sys.argv) > 1:
        token = sys.argv[1]

    if not token:
        print("Usage:")
        print("  python notion_dashboard.py <NOTION_TOKEN>")
        print("  or set NOTION_API_KEY in your .env file")
        sys.exit(1)

    result = create_power_dashboard(token)
    print(f"\nDashboard URL: {result['dashboard_url']}")
    print(f"Daily Planner DB: {result['daily_planner_db_id']}")
    print(f"Statistics DB: {result['statistics_db_id']}")
    for name, db_id in result["project_dbs"].items():
        print(f"{name} DB: {db_id}")
