import cv2
import os
import argparse
import subprocess

def highlightFace(net, frame, conf_threshold=0.7):
    frameHeight = frame.shape[0]
    frameWidth = frame.shape[1]
    blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), [104, 117, 123], True, False)

    net.setInput(blob)
    detections = net.forward()
    faceBoxes = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > conf_threshold:
            x1 = int(detections[0, 0, i, 3] * frameWidth)
            y1 = int(detections[0, 0, i, 4] * frameHeight)
            x2 = int(detections[0, 0, i, 5] * frameWidth)
            y2 = int(detections[0, 0, i, 6] * frameHeight)
            faceBoxes.append([x1, y1, x2, y2])
    return faceBoxes

def get_gender_from_image(image_path):
    faceProto = "opencv_face_detector.pbtxt"
    faceModel = "opencv_face_detector_uint8.pb"
    genderProto = "gender_deploy.prototxt"
    genderModel = "gender_net.caffemodel"

    MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
    genderList = ['Male', 'Female']

    faceNet = cv2.dnn.readNet(faceModel, faceProto)
    genderNet = cv2.dnn.readNet(genderModel, genderProto)

    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Unable to load image '{image_path}'")
        return None

    faceBoxes = highlightFace(faceNet, image)
    if not faceBoxes:
        print(f"No face detected in {image_path}")
        return None
    else:
        # Process first detected face
        faceBox = faceBoxes[0]
        face = image[max(0, faceBox[1]):min(faceBox[3], image.shape[0]),
                     max(0, faceBox[0]):min(faceBox[2], image.shape[1])]

        blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
        genderNet.setInput(blob)
        genderPreds = genderNet.forward()
        gender = genderList[genderPreds[0].argmax()]
        return gender

def rename_images_in_directory(directory):
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):  # Process image files
            image_path = os.path.join(directory, filename)
            gender = get_gender_from_image(image_path)

            if gender:
                new_filename = f"{gender[0].lower()}_{filename}"
                new_image_path = os.path.join(directory, new_filename)

                os.rename(image_path, new_image_path)
                print(f"Renamed '{filename}' to '{new_filename}'")

if __name__ == "__main__":
    directory = "./generated_faces"
    rename_images_in_directory(directory)
