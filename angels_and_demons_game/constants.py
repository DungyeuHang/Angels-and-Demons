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
        "label": "Classic",
        "description": "Tran dau mot van, giu nguyen luat co ban va tuy chinh cua ban.",
    },
    "solo_bot": {
        "label": "Solo vs Bot",
        "description": "Nguoi choi dau tien doi dau mot bot AI, hop de test nhanh va luyen tay.",
    },
    "challenge": {
        "label": "Challenge",
        "description": "Ap bo luat thu thach co san, effect kho hon va bo cuc bat ngo hon.",
    },
    "best_of_three": {
        "label": "Best of 3",
        "description": "Cho den khi co nguoi dat 2 van thang. Hop voi cac keo doi khang vui.",
    },
}

MATCH_PRESETS = {
    "quick": {
        "label": "Nhanh",
        "num_boxes": 24,
        "description": "Tran ngan, vao game nhanh va nhieu pha lat o lien tiep.",
    },
    "classic": {
        "label": "Co dien",
        "num_boxes": 50,
        "description": "Dung kich co quen thuoc, can bang cho nhom ban.",
    },
    "marathon": {
        "label": "Duong dai",
        "num_boxes": 72,
        "description": "Van dai hoi hon, hop voi custom va nhieu nguoi choi.",
    },
}

CHALLENGE_PRESETS = {
    "chaos_trial": {
        "label": "Chaos Trial",
        "description": "Layout Chaos, effect dac biet mo khoa va nhieu pha dao chieu hon.",
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
        "description": "Tran dai vua, layout Duel va nhieu co hoi bat combo diem dep.",
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
        "description": "Pha cuop diem va tru diem dan dac, hop cho ke nao thich keo kho.",
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
        "description": "Tien tri, Keo bua bao va doi menh xuat hien nhieu hon de danh lua doi thu.",
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
        "label": "Classic",
        "columns": 10,
        "box_size": 72,
        "gap": 12,
        "description": "Luoi rong, quen mat va can doi.",
    },
    "duel": {
        "label": "Duel",
        "columns": 8,
        "box_size": 78,
        "gap": 14,
        "description": "O to hon, de tap trung vao tung pha mo o.",
    },
    "tower": {
        "label": "Tower",
        "columns": 6,
        "box_size": 84,
        "gap": 16,
        "description": "Ban cao hon, cam giac nhu leo tang.",
    },
    "chaos": {
        "label": "Chaos",
        "columns": 7,
        "box_size": 76,
        "gap": 14,
        "description": "Can doi giua do dai va do rong, nhin la thay vui.",
    },
}

AI_LEVELS = {
    "easy": {
        "label": "De",
        "description": "Bot hay mo ngau nhien, thinh thoang moi tranh bay.",
        "think_delay_ms": 760,
        "preview_bias": 0.35,
    },
    "normal": {
        "label": "Vua",
        "description": "Bot uu tien o da duoc preview va tranh effect xau ro rang.",
        "think_delay_ms": 620,
        "preview_bias": 0.7,
    },
    "smart": {
        "label": "Lau ca",
        "description": "Bot rat tham doi voi o ngon va tiet che truoc biet xau.",
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
        "title": "Tran dau tien",
        "description": "Hoan thanh mot van choi bat ky.",
    },
    "angel_favored": {
        "title": "Duoc do ho",
        "description": "Mo hieu ung Thien than it nhat 3 lan trong mot tran.",
    },
    "loot_king": {
        "title": "Vua cuop diem",
        "description": "Cuop tong cong it nhat 60 diem trong mot tran.",
    },
    "lucky_burst": {
        "title": "Bung no diem",
        "description": "Co mot lan tang it nhat 50 diem trong mot turn.",
    },
    "marathon_clear": {
        "title": "Duong dai",
        "description": "Hoan thanh mot tran tu 70 o tro len.",
    },
    "bot_buster": {
        "title": "Ha guc AI",
        "description": "Danh bai bot o muc Lau ca.",
    },
    "effect_collector": {
        "title": "Nha suu tam",
        "description": "Trong su nghiep da mo du 8 hieu ung mac dinh.",
    },
    "challenge_cleared": {
        "title": "Pha dao thu thach",
        "description": "Hoan thanh va chien thang mot van Challenge.",
    },
    "series_champion": {
        "title": "Vo dich series",
        "description": "Thang tron mot keo Best of 3.",
    },
}
