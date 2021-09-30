"""
Test the pitch and note modules
"""
import pytest

from pyabc2.key import Key
from pyabc2.note import Note
from pyabc2.pitch import Pitch, PitchClass, SignedInterval, SimpleInterval, pitch_class_value


@pytest.mark.parametrize(
    ("name", "expected_value"),
    [
        ("C", 0),
        ("C#", 1),
        ("Db", 1),
        ("C###", 3),
        ("Eb", 3),
        ("Fbb", 3),
    ],
)
def test_pitch_value(name, expected_value):
    # using default root C
    assert pitch_class_value(name) == expected_value


@pytest.mark.parametrize(
    ("name", "expected_value"),
    [
        ("B##", 13),
        ("Cb", -1),
        ("Dbbb", -1),
    ],
)
def test_pitch_value_acc_outside_octave(name, expected_value):
    with pytest.warns(UserWarning):
        value = pitch_class_value(name)
    assert value == expected_value

    pitch_class_value(name, mod=True)  # no warning


@pytest.mark.parametrize("p", ["C", "Dbb"])
def test_C_variants(p):
    assert PitchClass.from_name("C") == PitchClass.from_name(p)


def test_equiv_sharp_flat():
    p0 = PitchClass.from_name("D")
    assert p0.equivalent_flat == PitchClass.from_name("Ebb")
    assert p0.equivalent_sharp == PitchClass.from_name("C##")


@pytest.mark.parametrize(
    ("d", "expected_new_name"),
    [
        (1, "C#"),
        (0, "C"),
        (-1, "B"),
        (12, "C"),
        (2, "D"),
        (5, "F"),
    ],
)
def test_add_int_to_C(d, expected_new_name):
    p0 = Pitch.from_name("C4")
    p = p0 + d
    assert p.class_name == expected_new_name

    pc0 = PitchClass.from_name("C")
    pc = pc0 + d
    assert pc.value == d


@pytest.mark.parametrize(
    ("d", "expected_new_name"),
    [
        (1, "B"),
        (0, "C"),
        (-1, "C#"),
        (12, "C"),
    ],
)
def test_sub_int_from_C(d, expected_new_name):
    p0 = PitchClass.from_name("C")
    p = p0 - d
    assert p.name == expected_new_name

    pc0 = PitchClass.from_name("C")
    pc = pc0 - d
    assert pc.value == -d


def test_eq():
    assert Pitch.from_name("C4") == Pitch.from_class_value(0, 4) == Pitch(48)
    assert Pitch.from_class_value(0, 4) != Pitch.from_class_value(0, 3)


def test_nice_names_from_values():
    ps = [PitchClass(i) for i in range(6)]
    assert [p.name for p in ps] == ["C", "C#", "D", "Eb", "E", "F"]


@pytest.mark.parametrize(("note", "octave", "expected_freq"), [("C", 4, 261.6256), ("A", 4, 440.0)])
def test_etf(note, octave, expected_freq):
    p = Pitch.from_name(f"{note}{octave}")
    assert p.equal_temperament_frequency == p.etf == pytest.approx(expected_freq)


def test_pitch_from_etf():
    Pitch.from_etf(440) == Pitch.from_name("A4")


def test_root_changing():
    p0 = PitchClass.from_name("C")
    p = p0.with_root("Bb")
    assert p0.name == p.name, "only value should be changing"
    assert p.value == 2


def test_pitch_class_to_pitch():
    C4 = Pitch.from_class_value(0, 4)

    assert PitchClass.from_name("C").to_pitch(4) == C4
    assert PitchClass.from_name("C", root="D").to_pitch(4) == C4


def test_pitch_to_pitch_class():
    D = PitchClass.from_name("D")

    assert Pitch(50).to_pitch_class() == D


# TODO: test add/mul Pitch(Class)


@pytest.mark.parametrize(
    ("abc", "expected_str_rep"),
    [
        # Octave
        ("C", "C4_1/8"),
        ("C,,", "C2_1/8"),
        ("C,,'", "C3_1/8"),
        #
        # Accidentals
        ("_B,2,", "Bb3_1/4"),
        ("^f", "F#5_1/8"),
        ("^^f',,3", "G4_3/8"),
        #
        # Relative duration
        ("C/", "C4_1/16"),
        ("C//", "C4_1/32"),
        ("C/3", "C4_1/24"),
    ],
)
def test_note_from_abc(abc, expected_str_rep):
    assert str(Note.from_abc(abc)) == expected_str_rep


def test_note_from_abc_key():
    assert Note.from_abc("F", key=Key("D")) == Note.from_abc("^F")


def test_note_to_from_abc_consistency():
    n = Note(49, duration=2)
    assert Note.from_abc(n.to_abc()) == n

    assert Note.from_abc(n.to_abc(key=Key("C#")), key=Key("C#")) == n


@pytest.mark.parametrize(
    ("v", "expected_name"),
    [
        (0, "P1"),
        (2, "M2"),
        (10, "m7"),
        (12, "P8"),
        (24, "P8"),
    ],
)
def test_simple_interval_name(v, expected_name):
    if 0 <= v <= 12:
        assert SimpleInterval(v).name == expected_name
    else:
        with pytest.warns(UserWarning):
            assert SimpleInterval(v).name == expected_name


@pytest.mark.parametrize(
    ("v", "expected_name"),
    [
        (0, "P1"),
        (2, "M2"),
        (3, "m3"),
        (15, "P8+m3"),
        (27, "2(P8)+m3"),
        (-27, "-[2(P8)+m3]"),
    ],
)
def test_signed_interval_name(v, expected_name):
    assert SignedInterval(v).name == expected_name


def test_interval_returned_from_pitch_sub():
    assert Pitch(50) - Pitch(40) == SignedInterval(10)
    assert Pitch(40) - Pitch(50) == SignedInterval(-10)
    assert PitchClass(7) - PitchClass(0) == SimpleInterval(7)
    with pytest.warns(UserWarning):
        assert PitchClass(0) - PitchClass(7) == SimpleInterval(7)


def test_add_interval_to_pitch():
    assert Pitch(40) + SignedInterval(-10) == Pitch(30)
    assert PitchClass(0) + SimpleInterval(5) == PitchClass(5)


def test_simple_interval_inverse():
    m3 = SimpleInterval.from_name("m3")
    assert m3.value == 3
    assert m3.inverse.name == "M6"
