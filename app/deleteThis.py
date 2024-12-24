import cv2
import mediapipe as mp
import numpy as np

import matplotlib.pyplot as plt

class CvMask():
    def __init__(self, path_to_image: str):
        # Инициализация объектов для отслеживания лица
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        # Загрузка масок
        self.mask = cv2.imread(path_to_image, cv2.IMREAD_UNCHANGED)
    
    # Функция для наложения маски на лицо
    def __apply_mask(self, image, mask, landmarks):
        h, w, _ = image.shape

        # Определение ключевых точек для масштабирования
        left_cheek = landmarks[234]  # Левая щека
        right_cheek = landmarks[454]  # Правая щека
        chin = landmarks[152]  # Подбородок
        forehead = landmarks[10]  # Лоб

        # Рассчитываем размер маски на основе расстояния между щеками и высоты лица
        cheek_distance = int(np.sqrt((right_cheek.x - left_cheek.x) ** 2 + (right_cheek.y - left_cheek.y) ** 2) * w)
        face_height = int(np.sqrt((chin.x - forehead.x) ** 2 + (chin.y - forehead.y) ** 2) * h)

        # Увеличиваем размер маски в 2 раза
        new_width = int(cheek_distance * 2.2)
        new_height = int(face_height * 2.5)
        mask_resized = cv2.resize(mask, (new_width, new_height))

        # Вычисление центра лица для наложения маски
        center_x = int((left_cheek.x + right_cheek.x) / 2 * w)
        center_y = int((forehead.y + chin.y) / 2 * h)
        mask_x = center_x - new_width // 2
        mask_y = center_y - new_height // 2

        # Наложение маски с учетом прозрачности
        for i in range(mask_resized.shape[0]):
            for j in range(mask_resized.shape[1]):
                y, x = mask_y + i, mask_x + j
                if 0 <= y < h and 0 <= x < w:
                    alpha = mask_resized[i, j, 3] / 255.0  # Нормализуем альфа-канал
                    image[y, x] = (1 - alpha) * image[y, x] + alpha * mask_resized[i, j, :3]

    def process_frame(self, frame):
        with self.mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, min_detection_confidence=0.5) as face_mesh:
            # Преобразование изображения в формат RGB
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            # Обнаружение ключевых точек лица
            results = face_mesh.process(image)

            # Обратно в формат BGR для отображения
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # Наложение маски при обнаружении лица
            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    landmarks = face_landmarks.landmark

                    # Вызываем функцию наложения маски
                    self.__apply_mask(image, self.mask, landmarks)
        return image
    


# img = cv2.imread('andrew.png', 1) 
# # # cv2.imshow("image", img)1
# # # cv2.waitKey(0)

# cv_mask = CvMask("mask1.png")
# processed_img = cv_mask.process_frame(img)
# cv2.imshow("image", processed_img)
# cv2.waitKey(0)
