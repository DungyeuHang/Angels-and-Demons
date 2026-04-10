APP_TITLE = "Angels and Demons"

DEFAULT_SETTINGS = {
    "music_enabled": True,
    "music_volume": 0.62,
    "sfx_enabled": True,
    "sfx_volume": 0.72,
    "fullscreen": False,
    "reduce_motion": False,
}

MODE_VARIANTS = {
    "standard": {
        "label": "Cổ điển",
        "description": "Trận đấu một ván, giữ nguyên luật cơ bản và tuỳ chỉnh của bạn.",
    },
    "challenge": {
        "label": "Thử thách",
        "description": "Áp bộ luật thử thách có sẵn, effect khó hơn và bố cục bất ngờ hơn.",
    },
    "best_of_three": {
        "label": "Đấu 3 ván",
        "description": "Chơi đến khi có người đạt 2 ván thắng. Hợp với các kèo đối kháng vui.",
    },
}

MATCH_PRESETS = {
    "quick": {
        "label": "Nhanh",
        "num_boxes": 24,
        "description": "Trận ngắn, vào game nhanh và nhiều pha lật ô liên tiếp.",
    },
    "classic": {
        "label": "Cổ điển",
        "num_boxes": 50,
        "description": "Dùng kích cỡ quen thuộc, cân bằng cho nhóm bạn.",
    },
    "marathon": {
        "label": "Đường dài",
        "num_boxes": 72,
        "description": "Ván dài hơi hơn, hợp với custom và nhiều người chơi.",
    },
}

CHALLENGE_PRESETS = {
    "chaos_trial": {
        "label": "Chaos Trial",
        "description": "Layout Chaos, effect đặc biệt mở khoá và nhiều pha đảo chiều hơn.",
        "match_preset": "quick",
        "layout_id": "chaos",
        "turn_mode": "sequential",
        "weights": {
            "angel": 0.9,
            "devil": 1.1,
            "gun": 1.0,
            "lucky": 0.8,
            "lottery": 0.8,
            "rps": 1.0,
            "double": 0.6,
            "half": 0.9,
            "shield": 0.5,
            "swap": 0.8,
            "reverse": 0.9,
            "oracle": 0.7,
        },
    },
    "halo_harvest": {
        "label": "Halo Harvest",
        "description": "Trận dài vừa, layout Duel và nhiều cơ hội bật combo điểm đẹp.",
        "match_preset": "classic",
        "layout_id": "duel",
        "turn_mode": "sequential",
        "weights": {
            "angel": 1.2,
            "devil": 0.6,
            "gun": 0.8,
            "lucky": 1.3,
            "lottery": 1.0,
            "rps": 0.8,
            "double": 0.9,
            "half": 0.4,
            "shield": 0.8,
            "swap": 0.3,
            "reverse": 0.2,
            "oracle": 0.5,
        },
    },
    "devils_gauntlet": {
        "label": "Devil's Gauntlet",
        "description": "Pha cướp điểm và trừ điểm dày đặc, hợp cho kẻ nào thích kèo khó.",
        "match_preset": "quick",
        "layout_id": "tower",
        "turn_mode": "sequential",
        "weights": {
            "angel": 0.4,
            "devil": 1.4,
            "gun": 1.3,
            "lucky": 0.6,
            "lottery": 0.4,
            "rps": 1.1,
            "double": 0.5,
            "half": 1.0,
            "shield": 0.3,
            "swap": 1.0,
            "reverse": 0.5,
            "oracle": 0.2,
        },
    },
    "mind_maze": {
        "label": "Mind Maze",
        "description": "Tiên tri, Kéo búa bao và đổi mệnh xuất hiện nhiều hơn để đánh lừa đối thủ.",
        "match_preset": "classic",
        "layout_id": "chaos",
        "turn_mode": "sequential",
        "weights": {
            "angel": 0.7,
            "devil": 0.8,
            "gun": 0.9,
            "lucky": 0.8,
            "lottery": 0.5,
            "rps": 1.2,
            "double": 0.6,
            "half": 0.7,
            "shield": 0.5,
            "swap": 1.0,
            "reverse": 0.8,
            "oracle": 1.1,
        },
    },
}

BOARD_LAYOUTS = {
    "classic": {
        "label": "Cổ điển",
        "columns": 10,
        "box_size": 72,
        "gap": 12,
        "description": "Lưới rộng, quen mắt và cân đối.",
    },
    "duel": {
        "label": "Duel",
        "columns": 8,
        "box_size": 78,
        "gap": 14,
        "description": "Ô to hơn, dễ tập trung vào từng pha mở ô.",
    },
    "tower": {
        "label": "Tower",
        "columns": 6,
        "box_size": 84,
        "gap": 16,
        "description": "Bàn cao hơn, cảm giác như leo tầng.",
    },
    "chaos": {
        "label": "Chaos",
        "columns": 7,
        "box_size": 76,
        "gap": 14,
        "description": "Cân đối giữa độ dài và độ rộng, nhìn là thấy vui.",
    },
}

AI_LEVELS = {
    "easy": {
        "label": "Dễ",
        "description": "Bot hay mở ngẫu nhiên, thỉnh thoảng mới tránh bẫy.",
        "think_delay_ms": 760,
        "preview_bias": 0.35,
    },
    "normal": {
        "label": "Vua",
        "description": "Bot ưu tiên ô đã được preview và tránh effect xấu rõ ràng.",
        "think_delay_ms": 620,
        "preview_bias": 0.7,
    },
    "smart": {
        "label": "Lão cá",
        "description": "Bot rất tham đối với ô ngon và tiết chế trước biết xấu.",
        "think_delay_ms": 460,
        "preview_bias": 1.0,
    },
}

EFFECT_AI_SCORES = {
    "angel": 48,
    "lucky": 40,
    "lottery": 60,
    "double": 45,
    "shield": 26,
    "oracle": 18,
    "rps": 20,
    "gun": 24,
    "swap": 18,
    "reverse": 10,
    "devil": -34,
    "half": -28,
}

ACHIEVEMENT_DEFINITIONS = {
    "first_match": {
        "title": "Trận đầu tiên",
        "description": "Hoàn thành một ván chơi bất kỳ.",
    },
    "angel_favored": {
        "title": "Được độ hộ",
        "description": "Mở hiệu ứng Thiên thần ít nhất 3 lần trong một trận.",
    },
    "loot_king": {
        "title": "Vua cướp điểm",
        "description": "Cướp tổng cộng ít nhất 60 điểm trong một trận.",
    },
    "lucky_burst": {
        "title": "Bùng nổ điểm",
        "description": "Có một lần tăng ít nhất 50 điểm trong một turn.",
    },
    "marathon_clear": {
        "title": "Đường dài",
        "description": "Hoàn thành một trận từ 70 ô trở lên.",
    },
    "effect_collector": {
        "title": "Nhà sưu tầm",
        "description": "Trong sự nghiệp đã mở đủ 8 hiệu ứng mặc định.",
    },
    "challenge_cleared": {
        "title": "Phá đảo thử thách",
        "description": "Hoàn thành và chiến thắng một ván Thử thách.",
    },
    "series_champion": {
        "title": "Vô địch series",
        "description": "Thắng trọn một kèo đấu 3 ván.",
    },
}
