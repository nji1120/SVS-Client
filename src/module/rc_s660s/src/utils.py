def print_hex(label: str, data: list[int]) -> None:
    """
    任意のバイト列やリストを16進数で見やすく出力するデバッグ用関数
    """
    # bytes型でなければbytesに変換
    if not isinstance(data, (bytes, bytearray)):
        data = bytes(data)
    hexstr = ' '.join(f'{b:02X}' for b in data)
    print(f"{label}: {hexstr}")


def extract_bytes(data: bytes, start_index: int, end_index: int) -> bytes:
    """
    バイト列の指定した範囲を抽出する
    """
    return data[start_index:end_index]