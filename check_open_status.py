import datetime
import os

def check_pizzaria_status():
    """
    Verifica se a Pizzaria Colonial está aberta com base no horário atual
    e nas regras definidas em val_conhecimento.txt
    """
    now = datetime.datetime.now()
    weekday = now.weekday()  # 0 = Segunda, 6 = Domingo
    current_time = now.time()

    # Definição dos horários
    # Seg-Qui: 18h às 23h30
    # Sex-Sáb: 18h às 00h
    # Dom: 18h às 23h30

    is_open = False

    if 0 <= weekday <= 3:  # Segunda a Quinta
        start = datetime.time(18, 0)
        end = datetime.time(23, 30)
        is_open = start <= current_time <= end
    elif weekday == 4 or weekday == 5:  # Sexta e Sábado
        start = datetime.time(18, 0)
        # Aberto até meia-noite
        is_open = current_time >= start
    elif weekday == 6:  # Domingo
        start = datetime.time(18, 0)
        end = datetime.time(23, 30)
        is_open = start <= current_time <= end

    status = "ABERTA 🍕" if is_open else "FECHADA 😴"
    print(f"--- Status Pizzaria Colonial ---")
    print(f"Data/Hora Atual: {now.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"A pizzaria está: {status}")
    
    return is_open

if __name__ == "__main__":
    check_pizzaria_status()