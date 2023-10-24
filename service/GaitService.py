import mediapipe as mp
import cv2
import time 
import math
import os

class GaitService():
    def __init__(self, azureSession , mongoSession, fileName = "deformed.mov"):
        self.azureSession = azureSession
        self.mongoSession = mongoSession
        self.mpDraw = mp.solutions.drawing_utils
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose()

        self.fileName = fileName
        self.fullFilePath= os.path.join(os.path.join(os.getcwd(),'WDC2/data'), self.fileName)
        self.localFilePath = os.path.join('WDC2/data', self.fileName)

        self.cap= None
        
        self.leftAngleList = []
        self.rightAngleList = []
        self.leftLegAngle = None
        self.rightLegAngle = None
        self.prediction = "undetermined"
        self.imageExtensions = {'jpeg','jpg','png'}
        self.thresholdAngle=85


    def run(self):
        #self.getVideoFromAzure()
        self.gaitTracking()
        self.analyzeData()
        self.updateMongo()
        self.clearTrace()
    
    def getVideoFromAzure(self):

        self.azureSession.download_blob_to_file(self.fullFilePath,self.fileName)
    
    def clearTrace(self):
        os.remove(self.fullFilePath)

    def videoProcessing(self):

        self.cap = cv2.VideoCapture(self.localFilePath)

        pTime=0

        while True:
            success, img = self.cap.read()

            if img is not None:
                imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                results = self.pose.process(imgRGB)

                if results.pose_landmarks:
                    self.mpDraw.draw_landmarks(img,results.pose_landmarks,self.mpPose.POSE_CONNECTIONS)
                    for id, lm in enumerate(results.pose_landmarks.landmark):
                        h,w,c = img.shape
                        #print(id, lm)
                        cx,cy = lm.x*w,lm.y*h
                        cv2.circle(img,(int(cx),int(cy)),5,(255,0,0),cv2.FILLED)

                    Hip1 = results.pose_landmarks.landmark[24]
                    Hip2 = results.pose_landmarks.landmark[23]

                    U_right = results.pose_landmarks.landmark[32]
                    V_right = results.pose_landmarks.landmark[30]

                    U_left = results.pose_landmarks.landmark[29]
                    V_left = results.pose_landmarks.landmark[31]

                    leftFoot_theta,leftFoot_alpha = self.angleBetweenTwoLines((Hip1.x,Hip1.y),(Hip2.x,Hip2.y),
                                                                    (U_left.x,U_left.y),(V_left.x,V_left.y))
                    rightFoot_theta,rightFoot_alpha = self.angleBetweenTwoLines((Hip1.x,Hip1.y),(Hip2.x,Hip2.y),
                                                                    (U_right.x,U_right.y),(V_right.x,V_right.y))

                    leftKnee = results.pose_landmarks.landmark[25]
                    leftAnkle = results.pose_landmarks.landmark[27]

                    rightKnee = results.pose_landmarks.landmark[26]
                    rightAnkle = results.pose_landmarks.landmark[28]
                    
                    leftKnee_theta,leftKnee_alpha = self.angleBetweenTwoLines((Hip2.x,Hip2.y),(leftKnee.x,leftKnee.y),
                                                                        (leftKnee.x,leftKnee.y),(leftAnkle.x,leftAnkle.y))
                    rightKnee_theta,rightKnee_alpha = self.angleBetweenTwoLines((Hip1.x,Hip1.y),(rightKnee.x,rightKnee.y),
                                                                        (rightKnee.x,rightKnee.y),(rightAnkle.x,rightAnkle.y))

                    if leftKnee_theta<10:
                        self.leftAngleList.append(leftFoot_theta)

                    if rightKnee_theta<10:
                        self.rightAngleList.append(rightFoot_theta)

            else:
                break
            cTime = time.time()
            fps = 1/(cTime-pTime)
            pTime = cTime
            cv2.waitKey(1)
    
    def imageProcessing(self):

        img = cv2.imread(self.localFilePath)
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.pose.process(imgRGB)

        if results.pose_landmarks:
            self.mpDraw.draw_landmarks(img,results.pose_landmarks,self.mpPose.POSE_CONNECTIONS)
            for id, lm in enumerate(results.pose_landmarks.landmark):
                h,w,c = img.shape
                #print(id, lm)
                cx,cy = lm.x*w,lm.y*h
                cv2.circle(img,(int(cx),int(cy)),5,(255,0,0),cv2.FILLED)

                Hip1 = results.pose_landmarks.landmark[24]
                Hip2 = results.pose_landmarks.landmark[23]

                U_right = results.pose_landmarks.landmark[32]
                V_right = results.pose_landmarks.landmark[30]

                U_left = results.pose_landmarks.landmark[29]
                V_left = results.pose_landmarks.landmark[31]

                leftFoot_theta,leftFoot_alpha = self.angleBetweenTwoLines((Hip1.x,Hip1.y),(Hip2.x,Hip2.y),
                                                                    (U_left.x,U_left.y),(V_left.x,V_left.y))
                rightFoot_theta,rightFoot_alpha = self.angleBetweenTwoLines((Hip1.x,Hip1.y),(Hip2.x,Hip2.y),
                                                                    (U_right.x,U_right.y),(V_right.x,V_right.y))
                self.leftAngleList.append(leftFoot_theta)
                self.rightAngleList.append(rightFoot_theta)
        cv2.waitKey(1)

    def gaitTracking(self):

        print("Started GaitTracking")

        if  self.fileName.rsplit('.', 1)[1].lower() in self.imageExtensions:
            self.imageProcessing()
        else:
            self.videoProcessing()
    
        print("GaitTracking Complete")
        
    def analyzeData(self):
        if len(self.leftAngleList):
            self.leftLegAngle = sum(self.leftAngleList)/len(self.leftAngleList)
        if len(self.rightAngleList):
            self.rightLegAngle = sum(self.rightAngleList)/len(self.rightAngleList)
        if self.leftLegAngle<self.thresholdAngle or self.rightLegAngle<self.thresholdAngle:
            self.prediction = "Deformed"
        else:
            self.prediction = "Normal"
        print({"leftLeg":self.leftLegAngle,
                "rightLeg":self.rightLegAngle,
                "prediction":self.prediction})
    
    def updateMongo(self):
        data = {"$set": {"leftLeg":self.leftLegAngle,
                         "rightLeg":self.rightLegAngle,
                         "prediction":self.prediction}}

        query = {"_id":self.mongoSession.emptyDocId}
        return self.mongoSession.updateDoc(query,data)

    @staticmethod
    def angleBetweenTwoLines(P,Q,R,S):
        x1,y1=P
        x2,y2=Q
        x3,y3=R
        x4,y4=S

        slope_PQ = (y2-y1)/(x2-x1)
        slope_RS = (y4-y3)/(x4-x3)

        tan_theta = (slope_RS - slope_PQ)/(1+(slope_PQ*slope_RS))
        theta = abs(math.atan(tan_theta)*100)
        alpha = 180 - theta
        return theta, alpha