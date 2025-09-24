#include "importpage.hpp"
#include "ui_importpage.h"

ImportPage::ImportPage(QWidget *parent)
    : QWidget(parent), ui(new Ui::ImportPage) {
    ui->setupUi(this);
    page = PAGE::MAIN;
}

ImportPage::~ImportPage() {
    delete ui;
}

ImportPage::PAGE ImportPage::get_page() {
    return page;
}

void ImportPage::Landsat() {
    page = PAGE::CUSTOM_BANDS;
    ui->check_filenames_changed->hide();
    ui->verticalLayout->takeAt(2)->widget()->deleteLater();

    QWidget     *container = new QWidget(this);
    QGridLayout *lyt = new QGridLayout();
    QPushButton *ok = new QPushButton("Ok");
    ok->setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
    connect(ok, &QPushButton::clicked, [this, lyt]() {
        QList<QPair<QString, QString>> bands_files;
        for (int i = 0; i < lyt->rowCount() - 2; i++) {
            QLabel    *lbl = qobject_cast<QLabel *>(lyt->itemAtPosition(i, 0)->widget());
            QLineEdit *le = qobject_cast<QLineEdit *>(lyt->itemAtPosition(i, 1)->widget());
            QString    band = lbl->text().split(' ').last();
            QString    file = le->text();
            if (file.toLower().endsWith(".tif") || file.toLower().endsWith(".tiff")) {
                bands_files.append(QPair<QString, QString>{band, file});
            }
        }
        emit custom_files(bands_files);
    });

    int bands = 11;
    for (int i = 0; i < bands; i++) {
        QLabel      *lbl = new QLabel("Канал " + QString::number(i + 1));
        QLineEdit   *le = new QLineEdit();
        QPushButton *pb = new QPushButton("Обзор");
        connect(pb, &QPushButton::clicked, [this, le]() {
            QString f = QFileDialog::getOpenFileName(this, "Открыть файл", QDir::homePath(), "GeoTiff (*.tif *.tiff *.TIF *.TIFF)");
            if (f.toLower().endsWith(".tif") || f.toLower().endsWith(".tiff")) {
                le->setText(f);
            } else {
                emit bad_band(f);
            }
        });
        lyt->addWidget(lbl, i, 0);
        lyt->addWidget(le, i, 1);
        lyt->addWidget(pb, i, 2);
    }

    lyt->addWidget(ok, bands, 1);
    lyt->itemAtPosition(bands, 1)->setAlignment(Qt::AlignHCenter);
    container->setLayout(lyt);
    ui->verticalLayout->insertWidget(2, container);
    emit custom_bands_page();
}

void ImportPage::to_satellite_select_page() {
    page = PAGE::MAIN;
    ui->verticalLayout->takeAt(2)->widget()->deleteLater();
    ui->check_filenames_changed->show();
    on_check_filenames_changed_checkStateChanged(Qt::Checked);
}

void ImportPage::on_check_filenames_changed_checkStateChanged(const Qt::CheckState &arg1) {
    if (arg1 == Qt::Checked) {
        QWidget     *container = new QWidget(this);
        QHBoxLayout *lyt = new QHBoxLayout();
        QPushButton *pb_Landsat = new QPushButton("Landsat 8/9");
        QPushButton *pb_Sentinel = new QPushButton("Sentinel 2");
        connect(pb_Landsat, &QPushButton::clicked, this, &ImportPage::Landsat);

        lyt->addWidget(pb_Landsat);
        lyt->addWidget(pb_Sentinel);
        container->setLayout(lyt);
        ui->verticalLayout->insertWidget(2, container);
        ui->pb_open_dir->hide();
        ui->pb_open_files->hide();
        emit satellite_select_page();
    } else {
        ui->verticalLayout->takeAt(2)->widget()->deleteLater();
        ui->pb_open_dir->show();
        ui->pb_open_files->show();
    }
}

void ImportPage::on_pb_open_dir_clicked() {
    QDir dir = QFileDialog::getExistingDirectory(this, "Открыть директорию", QDir::homePath());
    emit directory(dir);
}

void ImportPage::on_pb_open_files_clicked() {
    QStringList filenames = QFileDialog::getOpenFileNames(this, "Открыть файлы", QDir::homePath(), "GeoTiff (*.tif *.tiff *.TIF *.TIFF)");
    emit files(filenames);
}
