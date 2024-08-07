import subprocess
import sys
from arg_parser import get_common_parser
import torch
import torch.nn as nn
import torch.optim as optim
from utils.utils import get_dummy_dataloader, save_model
from models.cnn import CNN
from models.resnet import ResNet
from models.inception import Inception
from models.densenet import DenseNet
from models.efficientnet import EfficientNet
from models.mobilenet import MobileNet
from models.vit import ViT
from utils.utils import load_data
import torchvision
import logging
import time

# Install dependencies from requirements.txt
subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

print(f"torchvision version: {torchvision.__version__}")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

def get_model_by_name(model_name):
    model_classes = {
        'CNN': CNN,
        'ResNet': ResNet,
        'Inception': Inception,
        'DenseNet': DenseNet,
        'EfficientNet': EfficientNet,
        'MobileNet': MobileNet,
        'ViT': ViT
    }
    if model_name in model_classes:
        return model_classes[model_name](num_classes=10)  # Ensure num_classes is passed
    else:
        raise ValueError(f"Model {model_name} is not supported.")

def get_criterion():
    return nn.CrossEntropyLoss()

def get_optimizer(model):
    return optim.SGD(model.parameters(), lr=0.001, momentum=0.9)

def train(args):
    # Check if GPU is available
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logging.info(f'Using device: {device}')

    model = get_model_by_name(args.model_name)
    model.to(device)
    criterion = get_criterion()
    optimizer = get_optimizer(model)

    if args.execution_mode == 'fast_local_mode':
        # Use DummyDataset for fast local training
        trainloader = get_dummy_dataloader(args.model_name)
    else:
        # Load the actual dataset for SageMaker training
        trainloader, _ = load_data(args.model_name, subsample=args.subsample, subsample_rate=args.subsample_rate)
    # Train the model using the train_model method from BaseModel
    model.train_model(trainloader, criterion, optimizer, args.epochs)

     # Save the model to S3 with versioning
    if args.execution_mode == 'aws_training':
        current_time = time.strftime("%Y%m%d-%H%M%S")
        if args.subsample:
            version = f"{args.model_name}_subsample_{args.subsample_rate}_{current_time}"
        else:
            version = f"{args.model_name}_{current_time}"
        save_model(model, f's3://{args.bucket_name}/model_{version}.pth')
        
def main():
    # Parse command-line arguments
    parser = get_common_parser()
    args = parser.parse_args()

    train(args)

if __name__ == '__main__':
    main()