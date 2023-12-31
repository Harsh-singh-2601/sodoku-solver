import cv2
from imutils import contours as cnt_sort
import numpy as np
from matplotlib import pyplot as plt
from prediction import predict
import sudoku_solver

def get_sudo_grid(name,size):
    #img = cv2.imread(name,0)
    img = name
    original = img.copy()
    #img = cv2.medianBlur(img,5)
    img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
    greymain = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
    
    th2 = cv2.adaptiveThreshold(greymain,255,cv2.ADAPTIVE_THRESH_MEAN_C,\
                cv2.THRESH_BINARY_INV,39,10)
    
    
    contours,heirarchy = cv2.findContours(th2,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    maxarea = 0
    cnt = contours[0]
    for i in contours:
        if cv2.contourArea(i)>maxarea:
            cnt = i
            maxarea = cv2.contourArea(i)
    blank = np.zeros(img.shape,np.uint8)
    image = cv2.drawContours(blank,[cnt],-1,(255,255,255),2)
    edges = cv2.Canny(image,40,150,apertureSize = 3)
    lines = cv2.HoughLines(edges,1,np.pi/180,100)
    createhor = []
    createver = []
    created = []
    anglediff=10
    rhodiff=10
    flag=0
    count = 2
    
    for line in lines:
        for (rho,theta) in line:
            flag=0
            for (rho1,theta1) in created:
                if abs(rho-rho1)<rhodiff and abs(theta-theta1)<anglediff:
                    flag=1
                    
            if flag==0:
                a = np.cos(theta)
                b = np.sin(theta)
                x0 = a*rho
                y0 = b*rho
                x1 = int(x0 + 1000*(-b))
                y1 = int(y0 + 1000*(a))
                x2 = int(x0 - 1000*(-b))
                y2 = int(y0 - 1000*(a))
                d = np.linalg.norm(np.array((x1,y1,0))-np.array((x2,y2,0)))
                cv2.line(img,(x1,y1),(x2,y2),(0,255,0),2)
                m=abs(1/np.tan(theta))
                if m<1:
                    createhor.append((rho,theta))
                else:
                    createver.append((rho,theta))
                created.append((rho,theta))
                
    points=[]
    for (rho,theta) in createhor:
        for (rho1,theta1) in createver:
            if (rho,theta)!=(rho1,theta1):
                a=[[np.cos(theta),np.sin(theta)],[np.cos(theta1),np.sin(theta1)]]
                b=[rho,rho1]
                cor=np.linalg.solve(a,b)
                if list(cor) not in points:
                    points.append(list(cor))
    
                
    points.sort()
    if (points[0][1]>points[1][1]):
        points[0],points[1]=points[1],points[0]
    if (points[-1][1]<points[-2][1]):
        points[-1],points[-2]=points[-2],points[-1]
    
    points[1],points[2]=points[2],points[1]
    for i in points:
        images = cv2.circle(image,(int(i[0]),int(i[1])),4,(0,0,255),-1)
    pts1 = np.float32(points)
    pts2 = np.float32([[0,0],[size,0],[0,size],[size,size]])
    M = cv2.getPerspectiveTransform(pts1,pts2)
    
    warped2 = cv2.warpPerspective(blank,M,(size,size))
    img = cv2.warpPerspective(original,M,(size,size))
    return img, original,pts1,pts2

def get_sudoku(img ,size=900):
    img = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
    thresh = cv2.adaptiveThreshold(img,255,cv2.ADAPTIVE_THRESH_MEAN_C,\
                    cv2.THRESH_BINARY_INV,39,10)
    thresh1 = thresh.copy()
    kernel = np.ones((1,1),np.uint8)
    thresh = cv2.morphologyEx(thresh,cv2.MORPH_OPEN,kernel)
    thresh = cv2.dilate(thresh,kernel,iterations=3)
    kernel = np.ones((1,10),np.uint8)
    thresh = cv2.morphologyEx(thresh,cv2.MORPH_CLOSE,kernel)
    kernel = np.ones((10,1),np.uint8)
    thresh = cv2.morphologyEx(thresh,cv2.MORPH_CLOSE,kernel)
    
    #contours,heirarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    thresh = cv2.bitwise_not(thresh)
    contours,heirarchy = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    blank = np.zeros(img.shape,np.uint8)
    finalContours = []
    for cnt in contours:
        epsilon = 0.04*cv2.arcLength(cnt,True)
        approx = cv2.approxPolyDP(cnt,epsilon,True)
        approx = cv2.convexHull(cnt)
        area = cv2.contourArea(approx)
        if area <= 9000:
            finalContours.append(approx)
    sudoku_rows,_ = cnt_sort.sort_contours(finalContours,method="left-to-right")
    kernel = np.ones((3,3),np.uint8)
    thresh1 = cv2.erode(thresh1,kernel,iterations=1)
    blank_base = blank.copy()
    for c in sudoku_rows:
        blank = cv2.drawContours(blank,[c],-1,(255),-1)
        blank_base = cv2.drawContours(blank_base,[c],-1,(255),-1)
        blank = cv2.bitwise_and(thresh1,blank,mask=blank)
    
    kernel = np.ones((5,1),np.uint8)
    blank = cv2.erode(blank,kernel,iterations=1)
    kernel = np.ones((6,6),np.uint8)
    blank = cv2.morphologyEx(blank,cv2.MORPH_CLOSE,kernel)
    kernel = np.ones((1,5),np.uint8)
    blank = cv2.erode(blank,kernel,iterations=1)
    kernel = np.ones((9,9),np.uint8)
    blank = cv2.morphologyEx(blank,cv2.MORPH_CLOSE,kernel)
    kernel = np.ones((6,6),np.uint8)
    blank = cv2.dilate(blank,kernel,iterations=1)
    factor = blank.shape[0]//9
    sudoku_unsolved = []
    for i in range(9):
        for j in range(9):
            part = blank[i*factor:(i+1)*factor, j*factor:(j+1)*factor ]
            part = cv2.resize(part,(28,28))
            cv2.imwrite("images/{}_{}.jpg".format(i,j),part)
            num,_ = predict(part)
            sudoku_unsolved.append(str(num))
    for i in range(10):
        cv2.line(blank,(0,factor*i),(blank.shape[1],factor*i),(255),2,2)
        cv2.line(blank,(factor*i,0),(factor*i,blank.shape[0]),(255),2,2)
    return blank, sudoku_unsolved
def solve_sudoku(sudoku_unsolved,shape):
    sudoku_image = np.zeros(shape,np.uint8)
    y=-1
    x=0
    sudoku_solved = sudoku_solver.solve("".join(sudoku_unsolved).replace("0","."))
    factor = shape[0]//9
    for num in sudoku_unsolved:
        if (x%9)==0:
            x=0
            y+=1
        textX = int( factor*x+factor/2 )
        textY = int( factor*y+factor/2 )
        font = cv2.FONT_HERSHEY_SIMPLEX
        if num!='0':
            cv2.putText(sudoku_image,str(num),(textX,textY),font,1,(255,255,255),6)
        x+=1
    
    for i in range(10):
        cv2.line(sudoku_image,(0,factor*i),(shape[1],factor*i),(255),2,2)
        cv2.line(sudoku_image,(factor*i,0),(factor*i,shape[0]),(255),2,2)
    
    return sudoku_solved,sudoku_image
def create_sudoku_img(sudoku_image,sudoku,sudoku_unsolved,with_lines = True):
    x=0
    y=-1
    sudoku_image = np.zeros(sudoku_image.shape,np.uint8)
    factor = sudoku_image.shape[0]//9
    for num in range(len(sudoku)):
        if (x%9)==0:
            x=0
            y+=1
        textX = int( factor*x+factor/2 )
        textY = int( factor*y+factor/2 + factor//4)
        font = cv2.FONT_HERSHEY_SIMPLEX
        if sudoku_unsolved[num] == '0':
            cv2.putText(sudoku_image,sudoku[num],(textX,textY),font,1.75,(0,255,255),4)
        x+=1
    if with_lines:
        for i in range(10):
            cv2.line(sudoku_image,(0,factor*i),(sudoku_image.shape[1],factor*i),(0),2,2)
            cv2.line(sudoku_image,(factor*i,0),(factor*i,sudoku_image.shape[0]),(0),2,2)
    return sudoku_image

def change_perspective_to_original(pts2,pts1,sudoku_image,original):
    M = cv2.getPerspectiveTransform(pts2,pts1)
    
    img = cv2.warpPerspective(sudoku_image,M,(original.shape[1],original.shape[0]))
    img = cv2.bitwise_not(img)
    img = cv2.bitwise_and(img,original)
    return img
