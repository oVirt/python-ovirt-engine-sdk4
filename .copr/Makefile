.PHONY: installdeps srpm

installdeps:
	dnf -y install git gzip python3-devel rpm-build sed

srpm: installdeps
        ./.generate-setup-files.sh
	./.automation/build-srpm.sh
	cp rpmbuild/SRPMS/*.src.rpm $(outdir)
