import multiprocessing
import time

# Получает элементы из канала.
def consumer(pipe):
    output_p, input_p = pipe
    output_p.send([100,101])
    input_p.close()   # Закрыть конец канала, доступный для записи
    while True:
        try:
            item = output_p.recv()
        except EOFError:
            break
        # Обработать элемент
        print(item)    # Заместите эту инструкцию фактической обработкой
    # Завершение
    print('Потребитель завершил работу')

# Создает элементы и помещает их в канал. Переменная sequence представляет
# итерируемый объект с элементами, которые требуется обработать.
def producer(sequence, input_p):
    for item in sequence:
        # Послать элемент в канал
        input_p.send(item)

if __name__ == '__main__':
    (output_p, input_p) = multiprocessing.Pipe()
    # Запустить процесс-потребитель
    cons_p = multiprocessing.Process(target=consumer,args=((output_p,input_p),))
    cons_p.start()

    # Закрыть в поставщике конец канала, доступный для чтения
    output_p.close()

    # Отправить элементы
    sequence = [1,2]
    producer(sequence, input_p)
    time.sleep(1)
    sequence = [3,4]
    producer(sequence, input_p)
    time.sleep(1)
    sequence = [5,6]
    producer(sequence, input_p)
    time.sleep(1)
    sequence = [7,8]
    producer(sequence, input_p)

    print(input_p.recv())

    # Сообщить об окончании, закрыв конец канала, доступный для записи
    time.sleep(5)
    print ('Входной канал закрыт')
    input_p.close()

    # Дождаться, пока завершится процесс-потребитель
    cons_p.join()
