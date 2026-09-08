import unittest
import numpy as np
from speech_motion import schedule,sample_video

class MotionTests(unittest.TestCase):
 def test_voice_changes_motion_speed_without_stopping(self):
  audio=np.r_[np.zeros(16000),np.sin(np.arange(16000)*.12)*.15,np.zeros(16000)]
  p,end,m=schedule(audio,16000,25,75)
  self.assertTrue(np.all(np.diff(p)>0));self.assertLess(p[20]-p[10],p[45]-p[35]);self.assertLessEqual(m['speed_max'],1.25)
 def test_segment_boundary_continuity(self):
  p,end,_=schedule(np.zeros(16000),16000,25,25,17.3);q,_,_=schedule(np.zeros(16000),16000,25,25,end)
  self.assertAlmostEqual(q[0]-p[-1],.8)
 def test_geometry_and_image_interpolate_together(self):
  frames=[np.full((4,4,3),0,np.uint8),np.full((4,4,3),100,np.uint8)]
  result,boxes,masks,lo,hi,t=sample_video(frames,np.array([[0,0,2,2],[2,2,4,4]]),np.ones((2,4,4)),np.array([.5,1.5]))
  self.assertTrue(np.all(result[0]==50));self.assertTrue(np.allclose(boxes[0],[1,1,3,3]));self.assertTrue(np.isfinite(masks).all())

if __name__=='__main__':unittest.main()
