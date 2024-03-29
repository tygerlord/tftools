# -*- coding: utf-8 -*-
"""tftools1.ipynb

Automatically generated by Colaboratory.

Original file is located at
	https://colab.research.google.com/drive/1bPJA81Ps59_qz_s_fEl0ywfSQGFF7xby

# TFTOOLS
"""

import math
import random
import shutil
import tempfile
import traceback

from pathlib import Path
from collections import Counter
from typing import AnyStr

import numpy as np
import tensorflow as tf

from tensorflow.keras.utils import to_categorical
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.preprocessing.image import save_img, array_to_img
from tensorflow.keras.callbacks import EarlyStopping

import matplotlib.pyplot as plt

from tqdm import tqdm

import cv2

"""# Balancing dir datas

Balancing dir size
"""

def adjust_data_size(data_dir: AnyStr):
	""" 
		Balancing data. 
		make copy of image to have same number of image in each classe  
	"""
	data_path = Path(data_dir)
	
	all_images = {}
		
	for classe_path in data_path.glob("*"):
		if not classe_path.is_dir():
			continue
		classe = classe_path.name
		all_images[classe] = list(classe_path.glob("*"))
		random.shuffle(all_images[classe])
	
	m = max([ len(x) for x in all_images.values() ])
	
	print("max is {}".format(m))
		
	for classe, images in all_images.items():
		print("{}:{}".format(classe, len(images)))
		nb_images = len(images)
		for i in range(0, m-nb_images):
			image = images[i % nb_images]
			destpath = image.with_name("{}".format(i)).with_suffix(image.suffix)
			shutil.copy(str(image), str(destpath))

"""# Model class

Define Model class
"""

class Model:

	def __init__(self,
				model: tf.keras.Model, 
				img_size: int, 
				name : str, 
				batch_size: int = 32, 
				model_file: AnyStr = None, 
				aug=None, 
				preprocessing_function=None, 
				callbacks=None, 
				verbose: bool = False,
				**kwargs):

		print("model type is {}".format(name))
		
		self.model = model

		if model_file is not None:
			print("Load model file {}".format(model_file))
			modelpath = Path(model_file)
   
			if modelpath.exists():
				self.model = tf.keras.models.load_model(str(modelpath))
			else:
				warnings.warn("{} file not found".format(model_file))
	
		self.model_name = name
		
		self.img_size = img_size
		
		self.batch_size = batch_size
		
		self.preprocessing_function = preprocessing_function
		
		self.aug = aug
		
		filepath = self.model_name + "_best.h5"
		cp = tf.keras.callbacks.ModelCheckpoint(filepath, 
												monitor='val_acc', 
												verbose=1, 
												save_best_only=True, 
												save_weights_only=False, 
												mode='auto', 
												save_freq='epoch')

		if callbacks is None:
			callbacks = [ cp ]
		else:
			callbacks += [ cp ]
			
		self.callbacks = [cp]
		
		print("callbacks {}".format(self.callbacks))

		if verbose:
			self.model.summary()
		

	def test_generator(self, data_dir: AnyStr, batch_size: int = 32, output_dir: AnyStr = "results", **kwargs):
		"""
			Test generator
			
			Output image in result dir
			
			TODO(fl): same image format
		"""

		preprocessing_function = self.preprocessing_function
		
		aug = self.aug
		
		data_dir = Path(data_dir)  
		
		img_size = self.img_size
		
		if False:
			aug = ImageDataGenerator(preprocessing_function=preprocessing_function)

		data_gen = aug.flow_from_directory(str(data_dir), 
			target_size=(img_size, img_size),
			batch_size=batch_size,
			shuffle=True)
		
		images, labels = next(data_gen)

		labels = list(labels.argmax(axis=1))
		
		basepath = Path(output_dir)
		basepath.mkdir(exist_ok=True)

		for i in range(0, len(images)):
			
			destpath = basepath / str(labels[i])
			destpath.mkdir(exist_ok=True)
			destpath = destpath / "{}.bmp".format(i)
			if preprocessing_function is not None:
				npimg = preprocessing_function(images[i], True)
			else:
				npimg = images[i]
			save_img(str(destpath), npimg)



	def predicts(self, data_dir: AnyStr, verbose: bool = False, classe_img: bool = False, **kwargs):
		"""
			Make predictions on datadir 
		"""

		model = self.model

		img_size = self.img_size
		
		data_dir = Path(data_dir)
		
		batch_size = self.batch_size

		preprocessing_function = self.preprocessing_function
		
		#dont use data augmentation
		aug = ImageDataGenerator(preprocessing_function=preprocessing_function)

		testgen = aug.flow_from_directory(
			str(data_dir), 
			target_size=(img_size, img_size),
			batch_size=batch_size,
			shuffle=False,
		)

		print(testgen.classes)
		
		all_categories = testgen.classes
		
		
		predicts_steps = (len(testgen.classes) // batch_size) + 1
		predicts = model.predict(testgen, verbose=1, steps=predicts_steps)
		
		
		predicts = list(np.argmax(predicts, axis=1))
		
		print(predicts)
		
		categories = testgen.class_indices

		values = []
		for i in range(0,len(categories)):
			values.append([0] * len(categories))
		
		inv_categories = { v : k for k,v in categories.items() }

		if verbose:	
			print("all_categories:")
			print([inv_categories[x] for x in all_categories])
			print("all_predictions:")
			print([inv_categories[x] for x in predicts])
		
		for i in range(0, len(predicts)):
			values[predicts[i]][all_categories[i]] += 1

		good_results = 0
		total_results = 0
		for i in range(0, len(categories)):
			print("{}".format(values[i]))
			good_results += values[i][i]
			total_results += sum(values[i])
		
		#badtext =""
		
		taux0 = "{0:.02f}".format(100.0*good_results/total_results)	
		print("{}/{} taux0={}%".format(good_results, total_results, taux0))

		good_results = 0
		for i in range(0, len(predicts)):
			if math.pow(predicts[i] - all_categories[i], 2) < 2:
				good_results += 1
			#else:
				#badtext += "{}  predict {} instead of {} image {}\n".format(i, inv_categories[predicts[i]], inv_categories[all_categories[i]], all_images[i])  

		taux1 = "{0:.02f}".format(100.0*good_results/total_results)	
		print("{}/{} taux1={}%".format(good_results, total_results, taux1))

		print("inv_categories={}".format(inv_categories))
		
		tf.print(tf.math.confusion_matrix(labels=all_categories, predictions=predicts, num_classes=len(categories)))
		
		#print(badtext)
		
		nb_images = len(all_categories)
		
		if classe_img:
			basepath = Path("results")
			basepath.mkdir(exist_ok=True)

			testgen.reset()
			
			for j in range(0, (nb_images//batch_size)+1):
				images, labels = next(testgen)
				for i in range(0, len(images)):
					index = (j*batch_size)+i
					destpath = basepath / inv_categories[predicts[index]]
					destpath.mkdir(exist_ok=True)
					destpath = destpath / "{}.bmp".format(index)
					if preprocessing_function is not None:
						npimg2 = preprocessing_function(images[i], True)
					else:
						npimg2 = images[i].astype('uint8')
					save_img(str(destpath), npimg2)

	def evaluate(self, data_dir: AnyStr, save_model: bool = False, **kwargs):
		"""
			Evaluate model accuraccy
		"""

		model = self.model

		img_size = self.img_size
		
		batch_size = self.batch_size
		
		aug = self.aug
		
		preprocessing_function = self.preprocessing_function
			
		#dont use data augmentation
		aug = ImageDataGenerator(preprocessing_function=preprocessing_function)
		
		testgen = aug.flow_from_directory(
			str(data_dir), 
			target_size=(img_size, img_size),
			batch_size=batch_size,
			shuffle=False
		)

		print("[INFO] evaluate")
		validation_steps = (len(testgen.classes) // batch_size) + 1
		loss, accuracy = model.evaluate(testgen, steps=validation_steps)

		filename = None
		if save_model:
			model_name = self.model_name
			filename = "{}_{:.2f}_{:.2f}.h5".format(model_name, loss, accuracy)
			model.save(filename) 

		print("loss: {:.2f}".format(loss))
		print("accuracy: {:.2f}".format(accuracy))

		return loss, accuracy, filename


	def train(self, data_dir: AnyStr, epochs: int = 100, initial_epoch: int = 0, class_weight='auto', **kwargs) -> AnyStr:
		"""
			Train the model
		"""

		model = self.model
		
		model_name = self.model_name
		
		aug = self.aug
		
		preprocessing_function = self.preprocessing_function

		img_size = self.img_size
		
		batch_size = self.batch_size
		
		callbacks = self.callbacks
				
		data_dir = Path(data_dir) 
		
		if class_weight == 'balancing':
			adjust_data_size(data_dir / "train")
			adjust_data_size(data_dir / "val")
		
			path_data_dir = Path(data_dir)
			
			traingen = aug.flow_from_directory(
				str(path_data_dir / "train"), 
				target_size=(img_size, img_size),
				batch_size=batch_size,
				#subset='training',
				shuffle=True
			)
			
			
			no_aug = ImageDataGenerator(preprocessing_function=preprocessing_function)
	
			testgen = no_aug.flow_from_directory(
				str(path_data_dir / "val"), 
				target_size=(img_size, img_size),
				batch_size=batch_size,
				#subset='validation',
				shuffle=True
			)
		else:

			traingen = aug.flow_from_directory(
				str(data_dir), 
				target_size=(img_size, img_size),
				batch_size=batch_size,
				subset='training',
				shuffle=True
			)

			testgen = aug.flow_from_directory(
				str(data_dir), 
				target_size=(img_size, img_size),
				batch_size=batch_size,
				subset='validation',
				shuffle=True
			)

			class_indices = traingen.class_indices
				
			nb_classes = len(class_indices)
			
			count_train = sum(Counter(traingen.classes).values())
			
			count_val = sum(Counter(testgen.classes).values())
		
			total = count_train + count_val 
	
			count_classes = Counter(traingen.classes) + Counter(testgen.classes)
		
			if class_weight == 'auto':
				# n_samples / (n_classes * count(y)
				class_weight = { k: ((1.0/v)*(total)/nb_classes) for k,v in count_classes.items() }

				
		print(class_weight)
		
		# simple early stopping
		# train the network
		print("[INFO] training w/ generator...")
		history = []
		try:
			history = model.fit(
				traingen,
				steps_per_epoch=(count_train // batch_size)+1,
				validation_data=testgen,
				validation_steps=(count_val // batch_size)+1,
				initial_epoch=initial_epoch,
				epochs=epochs,
				class_weight=class_weight,
				callbacks=callbacks)

			print(history)
				
			loss, accuracy, saveas = self.evaluate(data_dir, True)
		
			filename="{}_{:.2f}_{:.2f}_epochs{}.h5".format(model_name, loss, accuracy, epochs)
			print("model saved {}".format(filename))
			model.save(filename) 
		except:
			print(traceback.format_exc())
			filename = "{}_{:.2f}_{:.2f}_epochs{}.h5".format(model_name, 0, 0, 0)
			model.save(filename) 
			print("model saved {}".format(filename))
			#exit(1)
			return None
			

		print("Model:")	
		print("\tval_loss: {:.2f}".format(history.history["val_loss"][-1]))
		print("\tval_accuracy: {:.2f}".format(history.history["val_acc"][-1]))

		#Learning curves
		#Let’s take a look at the learning curves of the training and validation accuracy/loss when using the VGG16 base model.
		plt.plot(history.history['acc'])
		plt.plot(history.history['val_acc'])
		plt.title('model accuracy')
		plt.ylabel('accuracy')
		plt.xlabel('epoch')
		plt.legend(['train', 'test'], loc='upper left')
		plt.savefig('learning curve.png')
		plt.show()
		
		# summarize history for loss
		plt.plot(history.history['loss'])
		plt.plot(history.history['val_loss'])
		plt.title('model loss')
		plt.ylabel('loss')
		plt.xlabel('epoch')
		plt.legend(['train', 'test'], loc='upper left')
		plt.savefig('loss curve.png')
		plt.show()


		print("done!")
	
		return saveas

	def add_regularization(self, kernel_regularizer: tf.keras.regularizers = tf.keras.regularizers.l2(0.0001)):
		"""
			Add regularization to model
		"""

		if not isinstance(kernel_regularizer, tf.keras.regularizers.Regularizer):
			print("Regularizer must be a subclass of tf.keras.regularizers.Regularizer")
			return self

		model = self.model

		for layer in model.layers:
			for attr in ['kernel_regularizer']:
				if hasattr(layer, attr):
					print("set kernel_regularizer")
					setattr(layer, attr, kernel_regularizer)

		# When we change the layers attributes, the change only happens in the model config file
		model_json = model.to_json()

		# Save the weights before reloading the model.
		tmp_weights_path = Path(tempfile.gettempdir()) / 'tmp_weights.h5'
		model.save_weights(str(tmp_weights_path))

		# load the model from the config
		model = tf.keras.models.model_from_json(model_json)
		
		# Reload the model weights
		model.load_weights(str(tmp_weights_path), by_name=True)
		
		self.model = model

	def compile(self, *args, **kwargs):
		"""
			Convenient way to compile model after add_initializer for example
		"""
		self.model.compile(*args, **kwargs)

"""# VideoImageDataGenerator"""

class VideoImageDataGenerator(ImageDataGenerator):
	'''
		Like ImageDataGenerator but for directory containing video files

	'''
	
	class Source:
		def __init__(self, videopath):
			
			self.videopath = videopath
			self.cap = cv2.VideoCapture(str(videopath))
			
			print(self.cap.get(cv2.CAP_PROP_FRAME_COUNT), self.cap.get(cv2.CAP_PROP_POS_FRAMES), self.cap.get(cv2.CAP_PROP_FPS))
			
		def __len__(self):
			return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT) * self.cap.get(cv2.CAP_PROP_FPS)) 
			
	def __init__(self, *args, **kwargs):
		super(VideoImageDataGenerator, self).__init__(*args, **kwargs)

		self.sources = {}

	def flow_from_directory(self, directory, target_size=(256, 256), color_mode='rgb', 
		classes=None, class_mode='categorical', batch_size=32, shuffle=True, 
		seed=None, save_to_dir=None, save_prefix='', save_format='png', 
		follow_links=False, subset=None, interpolation='nearest'):
		
		directory = Path(directory)

		print("directory is {}".format(directory))

		if classes is None:
			classes = sorted(list(directory.glob("*")))
			
		print("classes = {}".format(classes))
		
		for classe in classes:
			sources_by_classe = []
			for videoname in classe.glob("*"):
				#cap = cv2.VideoCapture(str(videoname))
				src = self.Source(videoname)
				
				#print(cap.get(cv2.CAP_PROP_FRAME_COUNT), cap.get(cv2.CAP_PROP_POS_FRAMES), cap.get(cv2.CAP_PROP_FPS))
				#self.sources.append([ (cap, x) for x in range(0,int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))]) 
				sources_by_classe.append(src)
			self.sources[classe.parts[-1]] = sources_by_classe
				
		print("Found {} images in {} classes".format(0, classes))
		
		print(self.sources)
		
		
		for k,v in self.sources.items():
			#print(len(v[0]))
			print("{} => {}".format(k,sum([ len(x) for x in v]) ))
		
		
"""# Predicts tflite

Test predicts like tflite
"""

# def test_model_tflite(model_name, data_dir):
# 	data_dir = Path(data_dir) 
	
# 	all_images = list(data_dir.glob('*/*'))
# 	all_images = [str(path) for path in all_images]

# 	all_predictions = []
# 	all_categories = []

# 	data_size = len(all_images)
	
# 	print(data_size)
	
# 	interpreter = tf.lite.Interpreter(model_name)
# 	interpreter.allocate_tensors()

# 	input_details = interpreter.get_input_details()
# 	output_details = interpreter.get_output_details()

# 	for i in tqdm(range(len(all_images))):
# 		print("{} {}".format(str(all_images[i]), categories[Path(all_images[i]).parts[-2]]))
# 		#npimg, label = parse_data(str(all_images[i]), categories[Path(all_images[i]).parts[-2]]) 
		
# 		all_categories += [ label ]
		
# 		test = [ np.array(npimg) ]
				
# 		interpreter.set_tensor(input_details[0]['index'], test)

# 		interpreter.invoke()
		
# 		tflite_results = interpreter.get_tensor(output_details[0]['index'])

# 		all_predictions += [ int(np.argmax(tflite_results)) ]
		
		
# 	values = []
# 	for i in range(0,len(categories)):
# 		values.append([0] * len(categories))
	
# 	inv_categories = { v : k for k,v in categories.items() }
	
# 	print("all_categories:")
# 	print([inv_categories[x] for x in all_categories])
# 	print("all_predictions:")
# 	print([inv_categories[x] for x in all_predictions])
	
# 	for i in range(0, len(all_predictions)):
# 		values[all_predictions[i]][all_categories[i]] += 1
		
# 	for i in range(0,len(categories)):
# 		print("{}".format(values[i]))
