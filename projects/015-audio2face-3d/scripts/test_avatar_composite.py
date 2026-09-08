"""Pixel identity for subpixel, clipped, scaled and silent face composites."""
import unittest
import numpy as np
from performance_postprocess import composite
from benchmark_avatar_composite import full_composite

class CompositeTests(unittest.TestCase):
 def test_matches_full_canvas_math_at_edges_and_subpixel_scales(self):
  rng=np.random.default_rng(41);source=rng.integers(0,256,(150,180,3),dtype=np.uint8)
  face=rng.random((256,256,3),dtype=np.float32)*255;mask=rng.random((256,256),dtype=np.float32)
  for box in [(20.32,30.71,132.81,142.34),(-40.7,-15.8,120.3,98.2),(170.2,140.7,210.9,185.5),(-200,-200,400,500),(181,151,350,310),(-140,-150,-50,-60)]:
   for weight in [0,.01,.33,1]:
    with self.subTest(box=box,weight=weight):self.assertTrue(np.array_equal(composite(source,face,box,mask,weight),full_composite(source,face,box,mask,weight)))
if __name__=='__main__':unittest.main()
