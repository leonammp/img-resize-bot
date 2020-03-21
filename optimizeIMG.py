import os
import urllib.request
from urllib.parse import urlparse
from pathlib import Path
from PIL import Image
from selenium import webdriver
import json

class Bot():
	
	def __init__(self, main_url):
		# url principal
		self.main_url = main_url
		self.domain = urlparse(main_url).netloc
		# lista de urls percorridas
		self.crawled_urls = []
		# webdriver
		self.chrome = webdriver.Chrome('/path/to/driver') # coloque a pasta onde baixou o driver
		# diretorio atual do arquivo python
		self.current_path = os.getcwd()
		# informações das imagens
		self.config_images = {}
		self.chrome.get(main_url)
		# pegar todas as urls do site
		self.crawler(main_url)
		for url in self.crawled_urls:
			# procura as imagens do site
			self.search_imgs(url)
		# redimenciona as imagem
		self.resize_imgs()

	# pega todos os links da url recursivamente
	def crawler(self, url):
		self.crawled_urls.append(url)
		self.chrome.get(url)
		urls = self.chrome.find_elements_by_xpath("//a[@href]")
		for a in urls:
			href = a.get_attribute('href')
			# se é uma url do mesmo dominio
			if self.is_valid_domain(href):
				print('\t[ LINK ] => ' + href)
				self.crawler(href)
				break
	
	# verifica se a url é válida
	def is_valid_domain(self, url):
		first_time = url not in self.crawled_urls
		same_domain = urlparse(url).netloc == self.domain
		return (first_time and same_domain)

	# verifica se é uma imagem válida
	def is_img(self, src):
		return not ('base64' in src or '.svg' in src)

	# procura as imagens da url
	def search_imgs(self, url):
		print('Procurando imagens em: ' + url)
		self.chrome.get(url)
		self.chrome.maximize_window()
		# array com todas as images do site
		images = self.chrome.find_elements_by_tag_name('img')
		self.download_imgs(images)

	# baixa as imagens da url
	def download_imgs(self, images):
		for img in images:
			# url da imagem
			img_url = img.get_attribute('src')
			# verificar se é uma imagem válida
			if self.is_img(img_url):
				url = urlparse(img_url)
				# diretório da imagem no site
				img_path = url.path.rpartition('/')[0]
				# pasta onde iremos salvar a imagem
				img_folder = img_path #se for windows .replace('/', '\\')
				# nome da imagem
				img_name = Path(url.path).name
				# caminho completo da imagem
				img_full_path = img_path+'/'+img_name
				# largura da imagem no html
				img_width = int(img.get_attribute('width'))
				# largura real da imagem
				img_real_width = int(img.get_attribute('naturalWidth'))
				# verificar se não baixou a imagem ainda
				if not img_full_path in self.config_images:
					# criar pasta para salvar a imagem
					Path(self.current_path + img_path).mkdir(parents=True, exist_ok=True)
					# caminho para salvar a imagem
					save_img_path = self.current_path + img_folder + '/' + img_name # se for windows '\\'
					# salvar imagem
					try:
						print('\t[ DOWNLOAD ] => ' + img_full_path)
						urllib.request.urlretrieve(img_url, save_img_path)
						# informações da imagem
						self.config_images[img_full_path] = {
							'img_width': img_width,
							'img_naturalWidth': img_real_width
						}
						with open('images_config.json', 'w') as f:
							json.dump(self.config_images, f)

					except Exception as e:
						print('[ ERRO ] Tentando baixar novamente => ' + img_full_path)
						urllib.request.urlretrieve(img_url, save_img_path)
				else:
					# se já baixou, verifica se a imagem está aparecento maior na tela
					# e define o novo tamanho para ser redimencionado depois
					if self.config_images[img_full_path]['img_width'] < img_width:
						self.config_images[img_full_path]['img_width'] = img_width 

		print('DOWNLOAD CONCLUÍDO')

	# redimenciona as imagens encontradas em todas as urls
	def resize_imgs(self):
		for image in self.config_images.keys():
			img_width = self.config_images[image]['img_width']
			img_naturalWidth = self.config_images[image]['img_naturalWidth']
			print('\t[ RESIZE ] => '+ image + ' [width ' + str(img_naturalWidth) + 'px TO ' + str(img_width) + 'px]')
			save_img_path = self.current_path + image
			# redimencionar imagem
			img = Image.open(save_img_path)
			wpercent = (img_width / float(img.size[0]))
			hsize = int((float(img.size[1]) * float(wpercent)))
			img = img.resize((img_width, hsize), Image.ANTIALIAS)
			img.save(save_img_path)
		print('RESIZE CONCLUÍDO')


if __name__ == '__main__':
	url = input('Insira a URL: ')
	Bot(url)