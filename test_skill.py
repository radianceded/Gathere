from skills.gathere_skill import run_gathere_skill

result = run_gathere_skill(
    participants=[
        {"name": "A", "address": "苏州大学独墅湖校区"},
        {"name": "B", "address": "苏州站"},
        {"name": "C", "address": "观前街"},
    ],
    keywords="火锅",
    city="苏州",
    mode="transit",
    top_k=3,
)

places = result.get("places", [])

for index, place in enumerate(places, start=1):
    print(f"\n推荐 {index}: {place.get('name')}")
    print(f"地址: {place.get('address')}")
    print(f"综合评分: {place.get('score')}")
    print(f"总通勤时间: {place.get('total_duration_min') or place.get('total_duration')} 分钟")
    print(f"最长单人通勤: {place.get('max_duration_min') or place.get('max_duration')} 分钟")
    print(f"公平性差值: {place.get('fairness_gap_min') or place.get('fairness_gap')} 分钟")

    print("每人通勤:")
    for route in place.get("routes", []):
        print(
            f"  - {route.get('participant')}: "
            f"{route.get('duration_min')} 分钟，"
            f"{route.get('distance_km')} km"
        )