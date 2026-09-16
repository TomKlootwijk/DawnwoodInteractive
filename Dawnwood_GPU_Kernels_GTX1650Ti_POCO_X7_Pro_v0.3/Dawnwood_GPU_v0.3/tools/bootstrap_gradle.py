"""Fetch the official pinned Gradle wrapper and verify the official checksum."""
from pathlib import Path
import hashlib, urllib.request
ROOT=Path(__file__).resolve().parents[1]
def get(url):
    with urllib.request.urlopen(url,timeout=45) as response:return response.read()
def main():
    root=ROOT/'android/gradle/wrapper';root.mkdir(parents=True,exist_ok=True)
    jar=get('https://raw.githubusercontent.com/gradle/gradle/v8.9.0/gradle/wrapper/gradle-wrapper.jar')
    checksum=get('https://services.gradle.org/distributions/gradle-8.9-wrapper.jar.sha256').decode().split()[0]
    if hashlib.sha256(jar).hexdigest()!=checksum:raise SystemExit('Gradle wrapper checksum mismatch')
    (root/'gradle-wrapper.jar').write_bytes(jar)
    distribution_sha=get('https://services.gradle.org/distributions/gradle-8.9-bin.zip.sha256').decode().split()[0]
    props=root/'gradle-wrapper.properties';text=props.read_text()
    if 'distributionSha256Sum=' not in text:props.write_text(text+'distributionSha256Sum='+distribution_sha+'\n')
    print('Official Gradle 8.9 wrapper verified:',checksum)
if __name__=='__main__':main()
