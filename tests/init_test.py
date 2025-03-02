from auto_easy.core.core import CoreConf, AutoCore

conf = CoreConf()
conf.window_id = 'Phone-9a'
# conf.pic_dir = os.path.join(os.path.dirname(__file__), 'det_pic/pics')
# conf.pic_save_dir = r'C:\Users\Administrator\Desktop\自动截图'
# conf.models = [yolo_dhxbx, yolo_fsdsyc1, yolo_nshy, yolo_adgd, yolo_lp, ai_ocr, ai_supper_res]
# conf.item_model_dir = os.path.join(root_path, 'biz/models')
auto_core = AutoCore(conf)
auto_core.show()
