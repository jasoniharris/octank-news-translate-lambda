import os
import boto3
import json
import string
from contextlib import closing
from botocore.exceptions import ClientError

def go(e,c):
  buck_src = os.environ['BUCK_SRC']
  buck_tar = os.environ['BUCK_TAR']
  file = e['Records'][0]['s3']['object']['key']
  outFile = file.replace('.json', '')
  print('Processing: ' + file)

  s3 = boto3.resource('s3')
  article = json.loads(s3.Object(buck_src, file).get()['Body'].read().decode('utf-8'))
  aHeadline = article['headline']
  aContent = article['content']

  client = boto3.client('translate')
  tHeadline = client.translate_text(Text=aHeadline,SourceLanguageCode='en',TargetLanguageCode='fr')['TranslatedText']
  tContent = client.translate_text(Text=aContent,SourceLanguageCode='en',TargetLanguageCode='fr')['TranslatedText']

  createText(buck_tar, outFile, 'english', aHeadline, aContent)
  createText(buck_tar, outFile, 'french', tHeadline, tContent)
  
  createMP3(buck_tar, outFile, 'english', os.environ['INTRO_EN'], aHeadline, aContent, os.environ['VOICE_EN'])
  createMP3(buck_tar, outFile, 'french', os.environ['INTRO_FR'], tHeadline, tContent, os.environ['VOICE_FR'])

def createText(bucket, outFile, language, headline, content):
  content = {'headline': headline, 'content': content}
  s3 = boto3.resource('s3')
  s3.Object(bucket, os.environ['OUTPUT_PATH_JSON'].replace('<LANG>',language).replace('<FILE>', outFile)).put(Body=json.dumps(content))

def createMP3(bucket, outFile, language, intro, headline, content, voice):
  rest = headline + '. ' + content
  if outFile == "1":
    rest = intro + rest

  textBlocks = []
  while (len(rest) > 1100):
    begin = 0
    end = rest.find(".", 1000)
    if (end == -1):
        end = rest.find(" ", 1000)
            
    textBlock = rest[begin:end]
    rest = rest[end:]
    textBlocks.append(textBlock)
      
  textBlocks.append(rest)            

  polly = boto3.client('polly')
  for textBlock in textBlocks: 
    response = polly.synthesize_speech(OutputFormat='mp3',Text=textBlock,VoiceId=voice)
          
    if "AudioStream" in response:
      with closing(response["AudioStream"]) as stream:
        output = os.path.join("/tmp/", language + outFile)
        with open(output, "ab") as file:
          file.write(stream.read())

  s3 = boto3.client('s3')
  s3.upload_file('/tmp/' + language + outFile, bucket, os.environ['OUTPUT_PATH_AUDIO'].replace('<LANG>',language).replace('<FILE>', outFile))
