from app.utils.red_flags import contains_red_flag


def test_red_flag_detection():
    assert contains_red_flag("mujhe chest pain ho raha hai") != []


def test_no_red_flag_for_mild_symptom():
    assert contains_red_flag("halka sar dard hai") == []
